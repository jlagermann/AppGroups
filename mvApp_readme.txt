mvApp.py

This is a python script for the purpose of moving large amounts of applications from one application group to another within the App Definition Groups on an SCC.  The script has 6 seperat options and some basic rules.

The fqdn of the SCC and the REST API access code for the SCC must be added to the script before it can be used.

Each one of the following options are exclusive options.  They cannot be used with any other option.
	-c			The collect option creates a defaultGroups.txt file from the current applications on the SCC.
	-r  		The restore option restores or moves all of the applications back to their default groups, as defined in the defaultGroups.txt file.  All custom applications will move to group 10.
	-g <group#> The group_restore option restores or moves all of the applications from an orginal group back to that group, as defined in the defaultGroups.txt file.
	
The following options are required to be used together.
	-f <group#>	The from_group option identifies the group to remove all of the applications from.  If the built_in_only option is not used, ALL applications in this group will be moved.
	-t <group#>	The to_group option identifies the group to move all of the applications from the from_group to.
	
Optional option for use with the from_group and to_group option.
	-b 		The built_in_only option will ensure that custom applications are not moved when used with the from_group and to_group options.
	
	
Some additional rules:
	The collect option should be ran before any other option so you have a backup to restore from.
	The group numbers must be between 1 and 10
		Current Application Group Id's 
			1: Business Bulk
			2: Business Critical
			3: Business Productivity
			4: Business Standard
			5: Business VDI
			6: Business Video
			7: Business Voice
			8: Recreational
			9: Standard Bulk
			10: Custom Applications