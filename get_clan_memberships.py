from time import sleep
import wom

async def get_memberships_in_clans(clan_group_id):
    """Check if players are members of other WOM groups, that can possibly be other clans."""
    client = wom.Client(
        user_agent="@LeviOhhhSsa",
        api_base_url="https://api.wiseoldman.net/v2",
    )

    await  client.start()

    result = await client.groups.get_details(clan_group_id)

    if result.is_ok:
        clan_details = result.unwrap()
        # Check each member
        for memb in clan_details.memberships:
            membership_in_clans = await client.players.get_group_memberships(username=memb.player.username)
            if membership_in_clans.is_ok:
                clans = membership_in_clans.unwrap()
                # Filter out groups with "team" in them, most likely used for bingo
                groups = [clan.group.name for clan in clans if "team" not in clan.group.name.lower()]
                if len(groups) > 1: # More than one group
                    print(f"Player {memb.player.username} is part of multiple WOM groups: {groups}")
            elif "Too Many Requests." in membership_in_clans.unwrap_err().message:
                # Number of requests is limited per minute, wait for that time and try again.
                sleep(60)
                membership_in_clans = await client.players.get_group_memberships(username=memb.player.username)
                if membership_in_clans.is_ok:
                    clans = membership_in_clans.unwrap()
                    groups = [clan.group.name for clan in clans if "team" not in clan.group.name.lower()]
                    if len(groups) > 1:
                        print(f"Player {memb.player.username} is part of multiple WOM groups: {groups}")
            else:
                # Error ocurred.
                print(f"Error: {membership_in_clans.unwrap_err()}")
                continue
    else:
        # Error ocurred.
        print(f"Error: {result.unwrap_err()}")
    await client.close()