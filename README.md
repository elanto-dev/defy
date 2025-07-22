### The scripts can be used to get the clan's data and compare it to the sheets

**NB!** The name of the Excel file should be set to 'defy.xlsx', or change the name in *main.py* script.

To run the script you need to create the Python environment, then run the sollowing python command:

```bash
python .\main.py arg1 arg2
```

Where **arg1** one is one of the following:
* *membs* - get and print data about group memberships of clan members;
* *get* - get and save data, don't compare to sheets;
* *run* - run script on pre-saved data (*get* command should be executed first)
* *all* - get and save WOM data and compare to sheets. Basically combines *'get'* and *'run'*, but takes longer to execute.

**arg2** is only used for *'run'* and *'all'* commands, where it is set to the last clan member's row from the Excel sheet.
