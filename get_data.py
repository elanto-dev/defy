import json
from time import sleep
import wom

async def save_leavers(clan_group_id : int):
    """ Get information about people leaving the clan and save it in the file. """
    client = wom.Client(
        user_agent="@LeviOhhhSsa",
        api_base_url="https://api.wiseoldman.net/v2",
    )

    await  client.start()

    leavers_list = []
    stop = False
    offset = 0
    while not stop:
        limit = 50
        leavers_results = await client.groups.get_activity(clan_group_id, limit=limit, offset=offset)
        if leavers_results.is_ok:
            # The result is ok, so we can unwrap here
            results = leavers_results.unwrap()
            if len(results) == 0:
                stop = True
            # Keep members who left
            left = [res for res in results if res.type == wom.GroupActivityType.Left]
            for activity in left:
                leavers_list.append((activity.created_at, activity.player.username))
        else:
            # Lets see what went wrong
            if "Too Many Requests." in leavers_results.unwrap_err().message:
                # Number of requests is limited per minute, wait for that time and try again.
                sleep(60)
                continue
            print(f"Error: {leavers_results.unwrap_err()}")
            stop = True
        offset = offset + limit
    await client.close()
    leavers_list = [(leaver[0].strftime("%Y-%m-%d %H:%M:%S"), leaver[1]) for leaver in sorted(leavers_list, key=lambda x: x[0])]
    with open('leavers.json', mode='w', encoding='utf-8') as file:
        json.dump(leavers_list, file)

async def save_namechanges(clan_group_id : int):
    """Get namechanges of the members and save them to the file."""
    client = wom.Client(
        user_agent="@LeviOhhhSsa",
        api_base_url="https://api.wiseoldman.net/v2",
    )
    await  client.start()

    namechanges_list = []
    stop = False
    offset = 0
    while not stop:
        limit = 50
        namechanges_results = await client.groups.get_name_changes(clan_group_id, limit=limit, offset=offset)
        if namechanges_results.is_ok:
            # The result is ok, so we can unwrap here
            namechanges = namechanges_results.unwrap()
            if len(namechanges) == 0:
                stop = True
            for namechange in namechanges:
                namechanges_list.append((namechange.created_at, namechange.old_name, namechange.new_name))
        else:
            # Lets see what went wrong
            if "Too Many Requests." in namechanges_results.unwrap_err().message:
                sleep(60)
                continue
            print(f"Error: {namechanges_results.unwrap_err()}")
            stop = True
        offset = offset + limit
    await client.close()
    # Sort by the datetime when name was changed
    namechanges_list = sorted(namechanges_list, key=lambda x: x[0])
    linked_namechanges = []
    for idx, element in enumerate(namechanges_list):
        # Add first one to list
        if idx == 0:
            linked_namechanges.append((element[1], element[2]))
            continue
        added = False
        # For the rest: either add it to the list, or append previously existing list of the namechanges for the same user.
        for lidx, linked_element in enumerate(linked_namechanges):
            if linked_element[-1] == element[1]:
                linked_el_list = list(linked_element)
                linked_el_list.append(element[2])
                appended_namechanges_tuple = tuple(linked_el_list)
                linked_namechanges[lidx] = appended_namechanges_tuple
                added = True
                break
        # If name was not previously changed, add the change to the main list
        if not added:
            linked_namechanges.append((element[1], element[2]))
    with open('namechanges.json', mode='w', encoding='utf-8') as file:
        json.dump(linked_namechanges, file)

async def get_nonactive_users(clan_group_id : int):
    """Get all the players whose status is not 'active"."""
    client = wom.Client(
        user_agent="@LeviOhhhSsa",
        api_base_url="https://api.wiseoldman.net/v2",
    )
    await  client.start()
    result = await client.groups.get_details(clan_group_id)
    non_active_players = []
    if result.is_ok:
        # The result is ok, so we can unwrap here
        details = result.unwrap()
        # Filter out players whose status is "active"
        non_active_players = [(member.player.username, member.player.status) \
                              for member in details.memberships \
                                if member.player.status != wom.PlayerStatus.Active]
    else:
        # Error encountered
        print(f"Error: {result.unwrap_err()}")
    await client.close()
    return non_active_players
