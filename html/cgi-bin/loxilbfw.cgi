#!/usr/bin/perl
###############################################################################
#                                                                             #
# IPFire.org - A linux based firewall                                         #
# Copyright (C) 2007-2011  IPFire Team  <info@ipfire.org>                     #
# Copyright (C) 2024  BPFire Team                                             #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
#                                                                             #
###############################################################################

use strict;

# enable only the following on debugging purpose
use warnings;
#use CGI::Carp 'fatalsToBrowser';

require '/var/ipfire/general-functions.pl';
require "${General::swroot}/lang.pl";
require "${General::swroot}/header.pl";

#workaround to suppress a warning when a variable is used only once
my @dummy = ( ${Header::colouryellow} );
undef (@dummy);

# Files used
my $setting = "${General::swroot}/main/settings";
our $datafile = "${General::swroot}/loxilb/fwconfig";		#(our: used in subroutine)

my %color = ();
my %mainsettings = ();
&General::readhash("${General::swroot}/main/settings", \%mainsettings);
&General::readhash("/srv/web/ipfire/html/themes/ipfire/include/colors.txt", \%color);

our %settings = ();

$settings{'EN'} = '';			# reuse for dummy field in position zero
$settings{'sourceIP'} = '';
$settings{'destinationIP'} = '';
$settings{'minSourcePort'} = '';
$settings{'maxSourcePort'} = '';
$settings{'minDestinationPort'} = '';
$settings{'maxDestinationPort'} = '';
$settings{'protocol'} = '';
$settings{'portName'} = '';
$settings{'preference'} = '';
$settings{'ruleAction'} = '';
my @nosaved=('EN','sourceIP','destinationIP','minSourcePort','maxSourcePort','minDestinationPort','maxDestinationPort','protocol','portName','preference','ruleAction');	# List here ALL setting2 fields. Mandatory

$settings{'ACTION'} = '';		# add/edit/remove
$settings{'KEY1'} = '';			# point record for ACTION

#Define each field that can be used to sort columns
my $sortstring='^sourceIP';
$settings{'SORT_sourceIPLIST'} = 'sourceIP';
my $errormessage = '';
my $warnmessage = '';

&Header::showhttpheaders();

#Get GUI values
&Header::getcgihash(\%settings);

###############
# DEBUG DEBUG
#&Header::openbox('100%', 'left', 'DEBUG');
#my $debugCount = 0;
#foreach my $line (sort keys %settings) {
#print "$line = $settings{$line}<br />\n";
# $debugCount++;
#}
#print "&nbsp;Count: $debugCount\n";
#&Header::closebox();
# DEBUG DEBUG
###############

# Load multiline data
our @current = ();
if (open(FILE, "$datafile")) {
    @current = <FILE>;
    close (FILE);
}

## Settings1 Box not used...
&General::readhash("${General::swroot}/main/settings", \%settings);


## Now manipulate the multi-line list with Settings2
# Basic actions are:
#	toggle the check box
#	add/update a new line
#	begin editing a line
#	remove a line


# Toggle enable/disable field.  Field is in second position
if ($settings{'ACTION'} eq $Lang::tr{'toggle enable disable'}) {
    #move out new line
    chomp(@current[$settings{'KEY1'}]);
    my @temp = split(/\,/,@current[$settings{'KEY1'}]);

    $temp[0] = $temp[0] ne '' ? '' : 'on';		# Toggle the field
    @current[$settings{'KEY1'}] = join (',',@temp)."\n";
    $settings{'KEY1'} = ''; 				# End edit mode

    &General::log($Lang::tr{'loxilb fw changed'});

    #Save current
    open(FILE, ">$datafile") or die 'loxilb fw datafile error';
    print FILE @current;
    close(FILE);

    # Rebuild configuration file
    #&BuildConfiguration;
}

if ($settings{'ACTION'} eq $Lang::tr{'add'}) {
	# Validate inputs
        if (!&General::validipandmask($settings{'sourceIP'})){
                $errormessage = $Lang::tr{'invalid ip'}." / ".$Lang::tr{'invalid netmask'};
        }else{
                #set networkip if not already correctly defined
                my($ip,$cidr) = split(/\//,$settings{'sourceIP'});
                $cidr = &General::iporsubtocidr($cidr);
                my $netip=&General::getnetworkip($ip,$cidr);
                $settings{'sourceIP'} = "$netip/$cidr";
        }

        if (!&General::validipandmask($settings{'destinationIP'})){
                $errormessage = $Lang::tr{'invalid ip'}." / ".$Lang::tr{'invalid netmask'};
        }else{
                #set networkip if not already correctly defined
                my($ip,$cidr) = split(/\//,$settings{'destinationIP'});
                $cidr = &General::iporsubtocidr($cidr);
                my $netip=&General::getnetworkip($ip,$cidr);
                $settings{'destinationIP'} = "$netip/$cidr";
        }

	#Check for already existing routing entry
	foreach my $line (@current) {
		chomp($line);				# remove newline
		my @temp=split(/\,/,$line);
		$temp[2] ='' unless defined $temp[2]; # destinationIP
		$temp[3] ='' unless defined $temp[2]; # minSourcePort
		$temp[4] ='' unless defined $temp[3]; # maxSourcePort
		$temp[5] ='' unless defined $temp[4]; # minDestinationPort
		$temp[6] ='' unless defined $temp[5]; # maxDestinationPort
		$temp[7] ='' unless defined $temp[6]; # protocol
		$temp[8] ='' unless defined $temp[7]; # portName
		$temp[9] ='' unless defined $temp[8]; # preference
		$temp[10] ='' unless defined $temp[9]; # ruleAction
		#Same ip already used?
		if($temp[1] eq $settings{'sourceIP'} && $settings{'KEY1'} eq ''){
			$errormessage = $Lang::tr{'ccd err loxilbconfigeexist'};
			last;
		}
	}

    unless ($errormessage) {
	if ($settings{'KEY1'} eq '') { #add or edit ?
	    unshift (@current, "$settings{'EN'},$settings{'sourceIP'},$settings{'destinationIP'},$settings{'minSourcePort'},$settings{'maxSourcePort'},$settings{'minDestinationPort'},$settings{'maxDestinationPort'},$settings{'protocol'},$settings{'portName'},$settings{'preference'},$settings{'ruleAction'}\n");
	    &General::log($Lang::tr{'loxilb lb config added'});
	} else {
	    @current[$settings{'KEY1'}] = "$settings{'EN'},$settings{'sourceIP'},$settings{'destinationIP'},$settings{'minSourcePort'},$settings{'maxSourcePort'},$settings{'minDestinationPort'},$settings{'maxDestinationPort'},$settings{'protocol'},$settings{'portName'},$settings{'preference'},$settings{'ruleAction'}\n";
	    $settings{'KEY1'} = '';       # End edit mode
	    &General::log($Lang::tr{'loxilb fw changed'});
	}

	if ($settings{'EN'} eq 'on') {
		&DeleteFW(%settings);
		&CreateFW(%settings);
	}

        # Write changes to config file.
        &SortDataFile;				# sort newly added/modified entry

	#map ($settings{$_}='' ,@nosaved);	# Clear fields
    }
}

if ($settings{'ACTION'} eq $Lang::tr{'edit'}) {
    #move out new line
    my $line = @current[$settings{'KEY1'}];	# KEY1 is the index in current
    chomp($line);
    my @temp = split(/\,/, $line);
    $settings{'EN'}=$temp[0];			# Prepare the screen for editing
    $settings{'sourceIP'}=$temp[1];
    $settings{'destinationIP'}=$temp[2];
    $settings{'minSourcePort'}=$temp[3];
    $settings{'maxSourcePort'}=$temp[4];
    $settings{'minDestinationPort'}=$temp[5];
    $settings{'maxDestinationPort'}=$temp[6];
    $settings{'protocol'}=$temp[7];
    $settings{'portName'}=$temp[8];
    $settings{'preference'}=$temp[9];
    $settings{'ruleAction'}=$temp[10];
    if ($settings{'EN'} eq 'on') {
	&CreateFW(%settings);
    }
}

if ($settings{'ACTION'} eq $Lang::tr{'remove'}) {

    my $line = @current[$settings{'KEY1'}];	# KEY1 is the index in current
    chomp($line);
    my @temp = split(/\,/, $line);
    $settings{'EN'}=$temp[0];			# Prepare the screen for editing
    $settings{'sourceIP'}=$temp[1];
    $settings{'destinationIP'}=$temp[2];
    $settings{'minSourcePort'}=$temp[3];
    $settings{'maxSourcePort'}=$temp[4];
    $settings{'minDestinationPort'}=$temp[5];
    $settings{'maxDestinationPort'}=$temp[6];
    $settings{'protocol'}=$temp[7];
    $settings{'portName'}=$temp[8];
    $settings{'preference'}=$temp[9];
    $settings{'ruleAction'}=$temp[10];

    &DeleteFW(%settings);

    splice (@current,$settings{'KEY1'},1);		# Delete line
    open(FILE, ">$datafile") or die 'route datafile error';
    print FILE @current;
    close(FILE);
    $settings{'KEY1'} = '';				# End remove mode
    &General::log($Lang::tr{'loxilb fw changed'});

    #&BuildConfiguration;				# then re-build conf which use new data
}

##  Check if sorting is asked
# If same column clicked, reverse the sort.
if ($ENV{'QUERY_STRING'} =~ /$sortstring/ ) {
    my $newsort=$ENV{'QUERY_STRING'};
    my $actual=$settings{'SORT_sourceIPLIST'};
    #Reverse actual sort ?
    if ($actual =~ $newsort) {
	my $Rev='';
	if ($actual !~ 'Rev') {
	    $Rev='Rev';
	}
	$newsort.=$Rev;
    }
    $settings{'SORT_sourceIPLIST'}=$newsort;
    map (delete ($settings{$_}) ,(@nosaved,'ACTION','KEY1'));# Must never be saved
    &General::writehash($setting, \%settings);
    &SortDataFile;
    $settings{'ACTION'} = 'SORT';			# Create an 'ACTION'
    map ($settings{$_} = '' ,@nosaved,'KEY1');		# and reinit vars to empty
}

if ($settings{'ACTION'} eq '' ) { # First launch from GUI
    # Place here default value when nothing is initialized
    $settings{'EN'} = 'on';
    $settings{'sourceIP'} = '';
    $settings{'destinationIP'} = '';
    $settings{'minSourcePort'} = '';
    $settings{'maxSourcePort'} = '';
    $settings{'minDestinationPort'} = '';
    $settings{'maxDestinationPort'} = '';
    $settings{'protocol'} = '';
    $settings{'portName'} = '';
    $settings{'preference'} = '';
    $settings{'ruleAction'} = '';
}

&Header::openpage($Lang::tr{'loxilb fw entries'}, 1, '');
&Header::openbigbox('100%', 'left', '', $errormessage);
my %checked=();     # Checkbox manipulations

if ($errormessage) {
    &Header::openbox('100%', 'left', $Lang::tr{'error messages'});
    print "<font class='base' color=red>$errormessage&nbsp;</font>";
    &Header::closebox();
}

#

$checked{'EN'}{'on'} = ($settings{'EN'} eq '' ) ? '' : "checked='checked'";

my $buttontext = $Lang::tr{'add'};
if ($settings{'KEY1'} ne '') {
    $buttontext = $Lang::tr{'update'};
    &Header::openbox('100%', 'left', $Lang::tr{'loxilb fw edit'});
} else {
    &Header::openbox('100%', 'left', $Lang::tr{'loxilb fw add'});
}

my @PROTOCOLS = ("any", "tcp", "udp", "icmp");
my @RULEACTIONS = ("allow", "drop");

#Edited line number (KEY1) passed until cleared by 'save' or 'remove' or 'new sort order'
print <<END;
<form method='post' action='$ENV{'SCRIPT_NAME'}'>
<input type='hidden' name='KEY1' value='$settings{'KEY1'}' />
<table width='100%'>
<tr>
    <td class='base'>$Lang::tr{'loxilb fw sourceIP'}&nbsp;<img src='/blob.gif' alt='*' /></td>
    <td><input type='text' name='sourceIP' value='$settings{'sourceIP'}' size='25'/></td>
</tr><tr>
    <td class='base'>$Lang::tr{'loxilb fw destinationIP'}&nbsp;<img src='/blob.gif' alt='*' /></td>
    <td><input type='text' name='destinationIP' value='$settings{'destinationIP'}' size='25'/></td>
    <td class='base'>$Lang::tr{'enabled'}</td>
    <td><input type='checkbox' name='EN' $checked{'EN'}{'on'} /></td>
</tr>
<tr>
    <td class='base'>$Lang::tr{'loxilb fw minSourcePort'}:&nbsp;</td>
    <td><input type='text' name='minSourcePort' value='$settings{'minSourcePort'}' size='25'/></td>
</tr>
<tr>
    <td class='base'>$Lang::tr{'loxilb fw maxSourcePort'}:&nbsp;</td>
    <td><input type='text' name='maxSourcePort' value='$settings{'maxSourcePort'}' size='25'/></td>
</tr>
<tr>
    <td class='base'>$Lang::tr{'loxilb fw minDestinationPort'}:&nbsp;</td>
    <td><input type='text' name='minDestinationPort' value='$settings{'minDestinationPort'}' size='25'/></td>
</tr>
<tr>
    <td class='base'>$Lang::tr{'loxilb fw maxDestinationPort'}:&nbsp;</td>
    <td><input type='text' name='maxDestinationPort' value='$settings{'maxDestinationPort'}' size='25'/></td>
</tr>
<tr>
    <td class='base'>$Lang::tr{'loxilb fw proto'}:&nbsp;</td>
    <td>
      <select name='protocol' id='protocol' style="width: 95px;">
END

# Insert the dynamic options for the 'PROTO' select element
  foreach (@PROTOCOLS) {
    print "<option value=\"$_\"";
    if ($_ eq $settings{'protocol'}) {
        print " selected=\"selected\"";
    }
    print ">$_</option>";
  }

print <<END;

     </select>
     </td>
</tr>

<tr>
    <td class='base'>$Lang::tr{'loxilb fw portName'}:&nbsp;</td>
    <td><input type='text' name='portName' value='$settings{'portName'}' size='25'/></td>
</tr>
<tr>
    <td class='base'>$Lang::tr{'loxilb fw preference'}:&nbsp;</td>
    <td><input type='text' name='preference' value='$settings{'preference'}' size='25'/></td>
</tr>

<tr>
    <td class='base'>$Lang::tr{'loxilb fw action'}:&nbsp;</td>
    <td>
      <select name='ruleAction' id='ruleAction' style="width: 95px;">
END

# Insert the dynamic options for the 'PROTO' select element
  foreach (@RULEACTIONS) {
    print "<option value=\"$_\"";
    if ($_ eq $settings{'ruleAction'}) {
        print " selected=\"selected\"";
    }
    print ">$_</option>";
  }

print <<END;

     </select>
     </td>
</tr>

</table>
<br>
<table width='100%'>
<tr>
    <td class='base' width='25%'><img src='/blob.gif' align='top' alt='*' />&nbsp;$Lang::tr{'required field'}</td>
    <td width='50%' align='right'><input type='hidden' name='ACTION' value='$Lang::tr{'add'}' /><input type='submit' name='SUBMIT' value='$buttontext' /></td>
</tr>
</table>
</form>
END

&Header::closebox();

&Header::openbox('100%', 'left', $Lang::tr{'loxilb fw entries'});
print <<END

<table width='100%' class='tbl'>
<tr>
    <th width='10%' align='center'><a href='$ENV{'SCRIPT_NAME'}?sourceIP'><b>$Lang::tr{'loxilb fw sourceIP'}</b></a></th>
    <th width='10%' align='center'><a href='$ENV{'SCRIPT_NAME'}?destinationIP'><b>$Lang::tr{'loxilb fw destinationIP'}</b></a></th>
    <th width='10%' align='center'><a href='$ENV{'SCRIPT_NAME'}?minSourcePort'><b>$Lang::tr{'loxilb fw minSourcePort'}</b></a></th>
    <th width='10%' align='center'><a href='$ENV{'SCRIPT_NAME'}?maxSourcePort'><b>$Lang::tr{'loxilb fw maxSourcePort'}</b></a></th>
    <th width='10%' align='center'><a href='$ENV{'SCRIPT_NAME'}?minDestinationPort'><b>$Lang::tr{'loxilb fw minDestinationPort'}</b></a></th>
    <th width='10%' align='center'><a href='$ENV{'SCRIPT_NAME'}?maxDestinationPort'><b>$Lang::tr{'loxilb fw maxDestinationPort'}</b></a></th>
    <th width='10%' align='center'><a href='$ENV{'SCRIPT_NAME'}?protocol'><b>$Lang::tr{'loxilb fw proto'}</b></a></th>
    <th width='10%' align='center'><a href='$ENV{'SCRIPT_NAME'}?portName'><b>$Lang::tr{'loxilb fw portName'}</b></a></th>
    <th width='10%' align='center'><a href='$ENV{'SCRIPT_NAME'}?preference'><b>$Lang::tr{'loxilb fw preference'}</b></a></th>
    <th width='10%' align='center'><a href='$ENV{'SCRIPT_NAME'}?ruleAction'><b>$Lang::tr{'loxilb fw action'}</b></a></th>
    <th width='10%' colspan='3' class='boldbase' align='center'><b>$Lang::tr{'action'}</b></th>
</tr>
END
;

#
# Print each line of @current list
#

my $key = 0;
my $col="";
foreach my $line (@current) {
    chomp($line);				# remove newline
    my @temp=split(/\,/,$line);
    $temp[2] ='' unless defined $temp[2]; # not always populated
    $temp[3] ='' unless defined $temp[2]; # not always populated
    $temp[4] ='' unless defined $temp[3]; # not always populated
    $temp[5] ='' unless defined $temp[4]; # not always populated
    $temp[6] ='' unless defined $temp[5]; # not always populated
    $temp[7] ='' unless defined $temp[6]; # not always populated
    $temp[8] ='' unless defined $temp[7]; # not always populated
    $temp[9] ='' unless defined $temp[8]; # not always populated
    $temp[10] ='' unless defined $temp[9]; # not always populated

    #Choose icon for checkbox
    my $gif = '';
    my $gdesc = '';
    if ($temp[0] ne '' ) {
	$gif = 'on.gif';
	$gdesc = $Lang::tr{'click to disable'};
    } else {
	$gif = 'off.gif';
	$gdesc = $Lang::tr{'click to enable'};
    }

    #Colorize each line
    if ($settings{'KEY1'} eq $key) {
	print "<tr bgcolor='${Header::colouryellow}'>";
    } elsif ($key % 2) {
	print "<tr>";
	$col="bgcolor='$color{'color20'}'";
    } else {
	print "<tr>";
	$col="bgcolor='$color{'color22'}'";
    }
    print <<END
<td align='center' $col>$temp[1]</td>
<td align='center' $col>$temp[2]</td>
<td align='center' $col>$temp[3]</td>
<td align='center' $col>$temp[4]</td>
<td align='center' $col>$temp[5]</td>
<td align='center' $col>$temp[6]</td>
<td align='center' $col>$temp[7]</td>
<td align='center' $col>$temp[8]</td>
<td align='center' $col>$temp[9]</td>
<td align='center' $col>$temp[10]</td>
<td align='center' $col>
<form method='post' action='$ENV{'SCRIPT_NAME'}'>
<input type='hidden' name='ACTION' value='$Lang::tr{'toggle enable disable'}' />
<input type='image' name='$Lang::tr{'toggle enable disable'}' src='/images/$gif' alt='$gdesc' title='$gdesc' />
<input type='hidden' name='KEY1' value='$key' />
</form>
</td>

<td align='center' $col>
<form method='post' action='$ENV{'SCRIPT_NAME'}'>
<input type='hidden' name='ACTION' value='$Lang::tr{'remove'}' />
<input type='image' name='$Lang::tr{'remove'}' src='/images/delete.gif' alt='$Lang::tr{'remove'}' title='$Lang::tr{'remove'}' />
<input type='hidden' name='KEY1' value='$key' />
</form>
</td>
</tr>
END
;
    $key++;
}
print "</table>";

# If table contains entries, print 'Key to action icons'
if ($key) {
print <<END
<table>
<tr>
    <td class='boldbase'>&nbsp;<b>$Lang::tr{'legend'}:&nbsp;</b></td>
    <td><img src='/images/on.gif' alt='$Lang::tr{'click to disable'}' /></td>
    <td class='base'>$Lang::tr{'click to disable'}</td>
    <td>&nbsp;&nbsp;</td>
    <td><img src='/images/off.gif' alt='$Lang::tr{'click to enable'}' /></td>
    <td class='base'>$Lang::tr{'click to enable'}</td>
    <td>&nbsp;&nbsp;</td>
    <td><img src='/images/delete.gif' alt='$Lang::tr{'remove'}' /></td>
    <td class='base'>$Lang::tr{'remove'}</td>
</tr>
</table>
END
;
}

&Header::closebox();

&Header::closebigbox();
&Header::closepage();

## Ouf it's the end !

# Sort the "current" array according to choices
sub SortDataFile
{
    our %entries = ();

    # Sort pair of record received in $a $b special vars.
    # When IP is specified use numeric sort else alpha.
    # If sortname ends with 'Rev', do reverse sort.
    #
    sub fixedleasesort {
	my $qs='';             # The sort field specified minus 'Rev'
	if (rindex ($settings{'SORT_sourceIPLIST'},'Rev') != -1) {
	    $qs=substr ($settings{'SORT_sourceIPLIST'},0,length($settings{'SORT_sourceIPLIST'})-3);
	    if ($qs eq 'sourceIP') {
		my @a = split(/\./,$entries{$a}->{$qs});
		my @b = split(/\./,$entries{$b}->{$qs});
		($b[0]<=>$a[0]) ||
		($b[1]<=>$a[1]) ||
		($b[2]<=>$a[2]) ||
		($b[3]<=>$a[3]);
	    } else {
		$entries{$b}->{$qs} cmp $entries{$a}->{$qs};
	    }
	} else { #not reverse
	    $qs=$settings{'SORT_sourceIPLIST'};
	    if ($qs eq 'sourceIP') {
		my @a = split(/\./,$entries{$a}->{$qs});
		my @b = split(/\./,$entries{$b}->{$qs});
		($a[0]<=>$b[0]) ||
		($a[1]<=>$b[1]) ||
		($a[2]<=>$b[2]) ||
		($a[3]<=>$b[3]);
	    } else {
		$entries{$a}->{$qs} cmp $entries{$b}->{$qs};
	    }
	}
    }

    #Use an associative array (%entries)
    my $key = 0;
    foreach my $line (@current) {
	chomp( $line); #remove newline because can be on field 5 or 6 (addition of REMARK)
	my @temp = ( '','','', '');
	@temp = split (',',$line);

	# Build a pair 'Field Name',value for each of the data dataline.
	# Each SORTABLE field must have is pair.
	# Other data fields (non sortable) can be grouped in one

	my @record = ('KEY',$key++,'EN',$temp[0],'sourceIP',$temp[1],'destinationIP',$temp[2],'minSourcePort',$temp[3],'maxSourcePort',$temp[4],'minDestinationPort',$temp[5],'maxDestinationPort',$temp[6],'protocol',$temp[7],'portName',$temp[8],'preference',$temp[9],'ruleAction',$temp[10]);
	my $record = {};                        	# create a reference to empty hash
	%{$record} = @record;                		# populate that hash with @record
	$entries{$record->{KEY}} = $record; 		# add this to a hash of hashes
    }

    open(FILE, ">$datafile") or die 'routing datafile error';

    # Each field value is printed , with the newline ! Don't forget separator and order of them.
    foreach my $entry (sort fixedleasesort keys %entries) {
	print FILE "$entries{$entry}->{EN},$entries{$entry}->{sourceIP},$entries{$entry}->{destinationIP},$entries{$entry}->{minSourcePort},$entries{$entry}->{maxSourcePort},$entries{$entry}->{minDestinationPort},$entries{$entry}->{maxDestinationPort},$entries{$entry}->{protocol},$entries{$entry}->{portName},$entries{$entry}->{preference},$entries{$entry}->{ruleAction}\n";
    }

    close(FILE);
    # Reload sorted  @current
    open (FILE, "$datafile");
    @current = <FILE>;
    close (FILE);
}

sub manageFW {
    my ($action, %settings) = @_;

    # Initialize variables
    my @loxicmd_options;
    my $command = 'loxicmd';
    my $firewallRule = "--firewallRule="; # Start quote

    # Construct firewall rule
    $firewallRule .= "sourceIP:$settings{'sourceIP'},destinationIP:$settings{'destinationIP'}";
    $firewallRule .= ",minSourcePort:$settings{'minSourcePort'}" if $settings{'minSourcePort'};
    $firewallRule .= ",maxSourcePort:$settings{'maxSourcePort'}" if $settings{'maxSourcePort'};
    $firewallRule .= ",minDestinationPort:$settings{'minDestinationPort'}" if $settings{'minDestinationPort'};
    $firewallRule .= ",maxDestinationPort:$settings{'maxDestinationPort'}" if $settings{'maxDestinationPort'};
    $firewallRule .= ",portName:$settings{'portName'}" if $settings{'portName'};

    if ($settings{'protocol'} eq "any") {
	$firewallRule .= ",protocol:0";
    } elsif ($settings{'protocol'} eq "tcp") {
	$firewallRule .= ",protocol:6";
    } elsif  ($settings{'protocol'} eq "udp") {
	$firewallRule .= ",protocol:17";
    } elsif ($settings{'protocol'} eq "icmp") {
	$firewallRule .= ",protocol:1";
    }

    $firewallRule .= ",preference:$settings{'preference'}" if $settings{'preference'};

    my $ruleAction = "--$settings{'ruleAction'}";

    # Push options for loxicmd
    if ($action eq "create") {
	push(@loxicmd_options, $action, "firewall", $firewallRule, $ruleAction);
    } else {
	push(@loxicmd_options, $action, "firewall", $firewallRule);
    }

    # Execute the command
    my $result = &General::system($command, @loxicmd_options);

    # Check for errors
    if ($result != 0) {
        print "Error: Failed to execute loxicmd command.\n";
        # You might want to add more detailed error handling here
    }
}

sub SaveFW {
    my @save_options;
    my $command = 'loxicmd';
    my $dir="/var/ipfire/loxilb/";
    push(@save_options, "save", "--firewall", "-c", $dir);
    &General::system_output($command, @save_options);
    #my @output = &General::system_output($command, @save_options);
    #$errormessage = join('', @output);
}

sub CreateFW {
    my (%settings) = @_;
    manageFW("create", %settings);
    &SaveFW;
}

sub DeleteFW {
    my (%settings) = @_;
    manageFW("delete", %settings);
    &SaveFW;
}
