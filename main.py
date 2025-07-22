
import asyncio
import json
import sys
from time import sleep
import wom
import pandas as pd
import get_data
import get_clan_memberships

async def get_wom_clam_members(group_id : int):
    """GET API data from WOM that includes all members who are in the clan with group_id."""
    client = wom.Client(
        user_agent="@LeviOhhhSsa",
        api_base_url="https://api.wiseoldman.net/v2",
    )
    await  client.start()
    result = await client.groups.get_details(group_id)
    wom_clan_members = []
    if result.is_ok:
        # The result is ok, so we can unwrap here
        details = result.unwrap()
        for member in details.memberships:
            wom_clan_members.append(member.player.username)
    else:
        # Error encountered
        print(f"Error: {result.unwrap_err()}")
    await client.close()
    return wom_clan_members

def to_list_of_strings(nested_list):
    """Recursive function: flattens any nested list of strings."""
    # Final string element
    if isinstance(nested_list, str):
        return [nested_list]
    # Not a string, flatten the list
    retlist = []
    for element in nested_list:
        retlist += to_list_of_strings(element)
    return retlist

def read_excel(last_col = 299):
    """ Read xlsx file with all the recorded members.
        Return the list of members where each member is either a list of one element: [main]; 
            or a list of two elements [main, alt]. """
    file_errors_location = './defy.xlsx'
    df = pd.read_excel(file_errors_location)
    members_list = []
    for idx in range(9, last_col-1):
        row = df.values[idx]
        if isinstance(row[4], float):
            members_list.append([str(row[3]).lower()])
        else:
            members_list.append([str(row[3]).lower(), str(row[4]).lower()])
    return members_list

def read_leavers_json():
    """Load data of members who left the clan."""
    with open('leavers.json', mode='r', encoding='utf-8') as f:
        leavers_data = json.load(f)
        return leavers_data


def read_namechanges_json():
    """Load data of members who changed their name."""
    with open('namechanges.json', mode='r', encoding='utf-8') as f:
        namechanges = json.load(f)
        normalised_namechanges = []
        for namechange in namechanges:
            normalised_namechanges.append([str(nc).lower() for nc in namechange])
        return normalised_namechanges

def main(last_row : int, group_id : int):
    """ Load data from the clan sheet, users who changed their name or left the clan, 
            and current WOM clan members.
        Compare the members from the sheet to current members or any changes.
        Creates an 'incorrect_clan_data.txt' file where all the changed to spreadsheets are added."""
    # Read data from excel sheet
    sheet_members_list = read_excel(last_row)
    wom_clan_members = asyncio.run(get_wom_clam_members(group_id)) # Get members from WOM
    assert(len(wom_clan_members) > 0) # Checl that WOM didn't fail
    clan_leavers_with_dates = read_leavers_json() # Get information about leaving the clan
    namechanges = read_namechanges_json() # Get all the namechanges
    non_active_members = asyncio.run(get_data.get_nonactive_users(group_id))
    changes_to_be_made = []
    incorrect_data_string = "" # String to be appended for the errors in sheets and WOM
    for non_active_member in non_active_members:
        changes_to_be_made.append(non_active_member[0])
        incorrect_data_string += f"User's '{non_active_member[0]}' status is {non_active_member[1]}.\n"
    for idx, member in enumerate(sheet_members_list):
        main_name = str(member[0]).lower()
        # Check for clan membership on main
        if main_name not in wom_clan_members:
            date_left = [date_user[0] for date_user in clan_leavers_with_dates if str(date_user[1]).lower() == main_name]
            # Check for namechanges first, as changing name can show up as leaving clan with old name.
            if any(main_name in usernames for usernames in namechanges):
                user_namechange = [usernames for usernames in namechanges if main_name in usernames][0]
                changes_to_be_made.append(user_namechange[-1])
                incorrect_data_string += f"Line {idx + 9}: '{main_name}' changed name to '{user_namechange[-1]}'.\n"
            # Check is left the clan.
            elif len(date_left) > 0:
                incorrect_data_string += f"Line {idx + 9}: '{main_name}' left clan on {date_left[0]}.\n"
            # No name
            else:
                incorrect_data_string += f"Line {idx + 9}: no data found for user '{main_name}'; " \
                    "possibly a typo in the name - check if player with similar name exists in the clan's WOM list below.\n"
        # If alt account exists - check for clan membership
        if len(member) > 1:
            alt_name = str(member[1]).lower()
            if alt_name not in wom_clan_members:
                date_left = [date_user[0] for date_user in clan_leavers_with_dates if str(date_user[1]).lower() == alt_name]
                # Check for namechanges first, as changing name can show up as leaving clan with old name.
                if any(alt_name in usernames for usernames in namechanges):
                    user_namechange = [usernames for usernames in namechanges if alt_name in usernames][0]
                    changes_to_be_made.append(user_namechange[-1])
                    incorrect_data_string += f"Line {idx + 9}: alt '{alt_name}' changed name to '{user_namechange[-1]}'.\n"
                elif len(date_left) > 0:
                    incorrect_data_string += f"Line {idx + 9}: alt '{alt_name}' left clan on {date_left[0]}.\n"
                else:
                    incorrect_data_string += f"Line {idx + 9}: no data found for user's alt '{alt_name}'; " \
                        "possibly a typo in the name - check if player with similar name exists in the clan's WOM list below.\n"
    collapsed_clan_list = to_list_of_strings(sheet_members_list) # Flatten users in the clan sheet
    for clan_member in wom_clan_members: # Check what members are in the clan, but not in the clan sheet
        # Check that member is in either clan list from sheets or changed their name that has to be fixed
        if clan_member not in collapsed_clan_list and clan_member not in changes_to_be_made:
            incorrect_data_string += f"Clan member '{clan_member}' is in the clan according to WOM, but not accounted for on the sheets.\n"
    with open('incorrect_clan_data.txt', mode='w', encoding='utf-8') as f:
        f.write(incorrect_data_string)

# Entry point for the script
if __name__ == "__main__":
    CLAN_GROUP_ID = 1028
    if len(sys.argv) == 1:
        print("Error: select one of the arguments: \n"
                "\t'membs' - get and print data about group memberships\n"
                "\t'get' - get and save data, don't compare to sheets\n"
                "\t'run' n - run script on pre-saved data, where n is the last row of members list\n"
                "\t'all' n - get and save data, compare to sheets, where n is the last row of members list")
    elif len(sys.argv) > 1 and sys.argv[1] == "membs":
        print("NB! This command takes lost time to run. Be patient!")
        asyncio.run(get_clan_memberships.get_memberships_in_clans(CLAN_GROUP_ID))
    elif len(sys.argv) > 1 and sys.argv[1] == "get":
        asyncio.run(get_data.save_namechanges(CLAN_GROUP_ID))
        sleep(60)
        asyncio.run(get_data.save_leavers(CLAN_GROUP_ID))
    elif len(sys.argv) > 1 and sys.argv[1] == "run" and len(sys.argv) == 3:
        main(int(sys.argv[2]), CLAN_GROUP_ID)
    elif len(sys.argv) > 1 and sys.argv[1] == "all" and len(sys.argv) == 3:
        asyncio.run(get_data.save_namechanges(CLAN_GROUP_ID))
        sleep(60)
        asyncio.run(get_data.save_leavers(CLAN_GROUP_ID))
        main(int(sys.argv[2]), CLAN_GROUP_ID)
    else:
        print("Error: select one of the arguments: \n"
                "\t'membs' - get and print data about group memberships\n"
                "\t'get' - get and save data, don't compare to sheets\n"
                "\t'run' n - run script on pre-saved data, where n is the last row of members list\n"
                "\t'all' n - get and save data, compare to sheets, where n is the last row of members list")