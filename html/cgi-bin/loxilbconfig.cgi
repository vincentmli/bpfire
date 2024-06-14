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
our $datafile = "${General::swroot}/loxilb/lbconfig";		#(our: used in subroutine)

my %color = ();
my %mainsettings = ();
&General::readhash("${General::swroot}/main/settings", \%mainsettings);
&General::readhash("/srv/web/ipfire/html/themes/ipfire/include/colors.txt", \%color);

our %settings = ();

$settings{'EN'} = '';			# reuse for dummy field in position zero
$settings{'NAME'} = '';
$settings{'EXTIP'} = '';
$settings{'PORT'} = '';
$settings{'PROTO'} = '';
$settings{'SEL'} = '';
$settings{'MODE'} = '';
$settings{'ENDPOINTS'} = '';
$settings{'EPORT'} = '';
$settings{'MONITOR'} = '';
my @nosaved=('EN','NAME','EXTIP','PORT','PROTO','SEL','MODE','ENDPOINTS','EPORT','MONITOR');	# List here ALL setting2 fields. Mandatory

$settings{'ACTION'} = '';		# add/edit/remove
$settings{'KEY1'} = '';			# point record for ACTION

#Define each field that can be used to sort columns
my $sortstring='^NAME';
$settings{'SORT_NAMELIST'} = 'NAME';
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

    &General::log($Lang::tr{'loxilb lb config changed'});

    #Save current
    open(FILE, ">$datafile") or die 'loxilb lbconfig datafile error';
    print FILE @current;
    close(FILE);

    # Rebuild configuration file
    #&BuildConfiguration;
}

if ($settings{'ACTION'} eq $Lang::tr{'add'}) {
	# Validate inputs
	if (!&General::validip($settings{'EXTIP'})){
		$errormessage = $Lang::tr{'invalid ip'};
	}

	if ($settings{'EXTIP'} =~ /^0\.0\.0\.0/){
		$errormessage = $Lang::tr{'invalid ip'}." - 0.0.0.0";
	}

	# Escape input in REMARK field
	$settings{'NAME'} = &Header::escape($settings{'NAME'});

	#Check for already existing routing entry
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
		#Same ip already used?
		if($temp[1] eq $settings{'NAME'} && $settings{'KEY1'} eq ''){
			$errormessage = $Lang::tr{'ccd err loxilbconfigeexist'};
			last;
		}
	}

    unless ($errormessage) {
	if ($settings{'KEY1'} eq '') { #add or edit ?
	    unshift (@current, "$settings{'EN'},$settings{'NAME'},$settings{'EXTIP'},$settings{'PORT'},$settings{'PROTO'},$settings{'SEL'},$settings{'MODE'},$settings{'ENDPOINTS'},$settings{'EPORT'},$settings{'MONITOR'}\n");
	    &General::log($Lang::tr{'loxilb lb config added'});
	} else {
	    @current[$settings{'KEY1'}] = "$settings{'EN'},$settings{'NAME'},$settings{'EXTIP'},$settings{'PORT'},$settings{'PROTO'},$settings{'SEL'},$settings{'MODE'},$settings{'ENDPOINTS'},$settings{'EPORT'},$settings{'MONITOR'}\n";
	    $settings{'KEY1'} = '';       # End edit mode
	    &General::log($Lang::tr{'loxilb lb config changed'});
	}

	if ($settings{'EN'} eq 'on') {
		&CreateLB(%settings);
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
    $settings{'NAME'}=$temp[1];
    $settings{'EXTIP'}=$temp[2];
    $settings{'PORT'}=$temp[3];
    $settings{'PROTO'}=$temp[4];
    $settings{'SEL'}=$temp[5];
    $settings{'MODE'}=$temp[6];
    $settings{'ENDPOINTS'}=$temp[7];
    $settings{'EPORT'}=$temp[8];
    $settings{'MONITOR'}=$temp[9];
    if ($settings{'EN'} eq 'on') {
	&CreateLB(%settings);
    }
}

if ($settings{'ACTION'} eq $Lang::tr{'remove'}) {

    my $line = @current[$settings{'KEY1'}];	# KEY1 is the index in current
    chomp($line);
    my @temp = split(/\,/, $line);
    $settings{'EN'}=$temp[0];			# Prepare the screen for editing
    $settings{'NAME'}=$temp[1];
    $settings{'EXTIP'}=$temp[2];
    $settings{'PORT'}=$temp[3];
    $settings{'PROTO'}=$temp[4];
    $settings{'SEL'}=$temp[5];
    $settings{'MODE'}=$temp[6];
    $settings{'ENDPOINTS'}=$temp[7];
    $settings{'EPORT'}=$temp[8];
    $settings{'MONITOR'}=$temp[9];
    &DeleteLB(%settings);

    splice (@current,$settings{'KEY1'},1);		# Delete line
    open(FILE, ">$datafile") or die 'route datafile error';
    print FILE @current;
    close(FILE);
    $settings{'KEY1'} = '';				# End remove mode
    &General::log($Lang::tr{'loxilb lb config changed'});

    #&BuildConfiguration;				# then re-build conf which use new data
}

##  Check if sorting is asked
# If same column clicked, reverse the sort.
if ($ENV{'QUERY_STRING'} =~ /$sortstring/ ) {
    my $newsort=$ENV{'QUERY_STRING'};
    my $actual=$settings{'SORT_NAMELIST'};
    #Reverse actual sort ?
    if ($actual =~ $newsort) {
	my $Rev='';
	if ($actual !~ 'Rev') {
	    $Rev='Rev';
	}
	$newsort.=$Rev;
    }
    $settings{'SORT_NAMELIST'}=$newsort;
    map (delete ($settings{$_}) ,(@nosaved,'ACTION','KEY1'));# Must never be saved
    &General::writehash($setting, \%settings);
    &SortDataFile;
    $settings{'ACTION'} = 'SORT';			# Create an 'ACTION'
    map ($settings{$_} = '' ,@nosaved,'KEY1');		# and reinit vars to empty
}

if ($settings{'ACTION'} eq '' ) { # First launch from GUI
    # Place here default value when nothing is initialized
    $settings{'EN'} = 'on';
    $settings{'NAME'} = '';
    $settings{'EXTIP'} = '';
    $settings{'PORT'} = '';
    $settings{'PROTO'} = '';
    $settings{'SEL'} = '';
    $settings{'MODE'} = '';
    $settings{'ENDPOINTS'} = '';
    $settings{'EPORT'} = '';
    $settings{'MONITOR'} = '';
}

&Header::openpage($Lang::tr{'loxilb lb config entries'}, 1, '');
&Header::openbigbox('100%', 'left', '', $errormessage);
my %checked=();     # Checkbox manipulations

if ($errormessage) {
    &Header::openbox('100%', 'left', $Lang::tr{'error messages'});
    print "<font class='base'>$errormessage&nbsp;</font>";
    &Header::closebox();
}

#

$checked{'EN'}{'on'} = ($settings{'EN'} eq '' ) ? '' : "checked='checked'";

my $buttontext = $Lang::tr{'add'};
if ($settings{'KEY1'} ne '') {
    $buttontext = $Lang::tr{'update'};
    &Header::openbox('100%', 'left', $Lang::tr{'loxilb lb edit'});
} else {
    &Header::openbox('100%', 'left', $Lang::tr{'loxilb lb add'});
}

my @PROTOCOLS = ("tcp", "udp");
my @ALGO = ("rr", "hash", "priority", "persist", "lc");
my @MODE = ("default", "onearm", "fullnat", "dsr");
my @MONITOR = ("on", "off");

#Edited line number (KEY1) passed until cleared by 'save' or 'remove' or 'new sort order'
print <<END;
<form method='post' action='$ENV{'SCRIPT_NAME'}'>
<input type='hidden' name='KEY1' value='$settings{'KEY1'}' />
<table width='100%'>
<tr>
    <td class='base'>$Lang::tr{'loxilb lb name'}:&nbsp;</td>
    <td><input type='text' name='NAME' value='$settings{'NAME'}' size='25'/></td>
</tr><tr>
    <td class='base'>$Lang::tr{'loxilb lb extip'}:&nbsp;</td>
    <td><input type='text' name='EXTIP' value='$settings{'EXTIP'}' size='25'/></td>
    <td class='base'>$Lang::tr{'enabled'}</td>
    <td><input type='checkbox' name='EN' $checked{'EN'}{'on'} /></td>
</tr>
<tr>
    <td class='base'>$Lang::tr{'loxilb lb port'}:&nbsp;</td>
    <td><input type='text' name='PORT' value='$settings{'PORT'}' size='25'/></td>
</tr>
<tr>
    <td class='base'>$Lang::tr{'loxilb lb proto'}:&nbsp;</td>
    <td>
      <select name='PROTO' id='protocol' style="width: 95px;">
END

# Insert the dynamic options for the 'PROTO' select element
  foreach (@PROTOCOLS) {
    print "<option value=\"$_\"";
    if ($_ eq $settings{'PROTO'}) {
        print " selected=\"selected\"";
    }
    print ">$_</option>";
  }

print <<END;

     </select>
     </td>
</tr>
<tr>
    <td class='base'>$Lang::tr{'loxilb lb sel'}:&nbsp;</td>
    <td>
        <select name='SEL' id='select' style="width: 95px;">
END

  foreach (@ALGO) {
    print "<option value=\"$_\"";
    if ($_ eq $settings{'SEL'}) {
        print " selected=\"selected\"";
    }
    print ">$_</option>";
  }

print <<END;

     </select>
     </td>

</tr>
<tr>
    <td class='base'>$Lang::tr{'loxilb lb mode'}:&nbsp;</td>
    <td>
        <select name='MODE' id='mode' style="width: 95px;">

END

  foreach (@MODE) {
    print "<option value=\"$_\"";
    if ($_ eq $settings{'MODE'}) {
        print " selected=\"selected\"";
    }
    print ">$_</option>";
  }

print <<END;

     </select>
     </td>

</tr>
<tr>
    <td class='base'>$Lang::tr{'loxilb lb endpoints'}:&nbsp;</td>
    <td><input type='text' name='ENDPOINTS' value='$settings{'ENDPOINTS'}' size='50'/></td>
</tr>
<tr>
    <td class='base'>$Lang::tr{'loxilb lb eport'}:&nbsp;</td>
    <td><input type='text' name='EPORT' value='$settings{'EPORT'}' size='25'/></td>
</tr>
<tr>
    <td class='base'>$Lang::tr{'loxilb lb monitor'}:&nbsp;</td>
    <td>
        <select name='MONITOR' id='monitor' style="width: 95px;">

END

  foreach (@MONITOR) {
    print "<option value=\"$_\"";
    if ($_ eq $settings{'MONITOR'}) {
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
    <td width='50%' align='right'><input type='hidden' name='ACTION' value='$Lang::tr{'add'}' /><input type='submit' name='SUBMIT' value='$buttontext' /></td>
</tr>
</table>
</form>
END

&Header::closebox();

&Header::openbox('100%', 'left', $Lang::tr{'loxilb lb config entries'});
print <<END

<table width='100%' class='tbl'>
<tr>
    <th width='10%' align='center'><a href='$ENV{'SCRIPT_NAME'}?NAME'><b>$Lang::tr{'loxilb lb name'}</b></a></th>
    <th width='10%' align='center'><a href='$ENV{'SCRIPT_NAME'}?EXTIP'><b>$Lang::tr{'loxilb lb extip'}</b></a></th>
    <th width='10%' align='center'><a href='$ENV{'SCRIPT_NAME'}?PORT'><b>$Lang::tr{'loxilb lb port'}</b></a></th>
    <th width='10%' align='center'><a href='$ENV{'SCRIPT_NAME'}?PROTO'><b>$Lang::tr{'loxilb lb proto'}</b></a></th>
    <th width='10%' align='center'><a href='$ENV{'SCRIPT_NAME'}?SEL'><b>$Lang::tr{'loxilb lb sel'}</b></a></th>
    <th width='10%' align='center'><a href='$ENV{'SCRIPT_NAME'}?MODE'><b>$Lang::tr{'loxilb lb mode'}</b></a></th>
    <th width='10%' align='center'><a href='$ENV{'SCRIPT_NAME'}?ENDPOINTS'><b>$Lang::tr{'loxilb lb endpoints'}</b></a></th>
    <th width='10%' align='center'><a href='$ENV{'SCRIPT_NAME'}?EPORT'><b>$Lang::tr{'loxilb lb eport'}</b></a></th>
    <th width='10%' align='center'><a href='$ENV{'SCRIPT_NAME'}?MONITOR'><b>$Lang::tr{'loxilb lb monitor'}</b></a></th>
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
<td align='center' $col>
<form method='post' action='$ENV{'SCRIPT_NAME'}'>
<input type='hidden' name='ACTION' value='$Lang::tr{'toggle enable disable'}' />
<input type='image' name='$Lang::tr{'toggle enable disable'}' src='/images/$gif' alt='$gdesc' title='$gdesc' />
<input type='hidden' name='KEY1' value='$key' />
</form>
</td>

<td align='center' $col>
<form method='post' action='$ENV{'SCRIPT_NAME'}'>
<input type='hidden' name='ACTION' value='$Lang::tr{'edit'}' />
<input type='image' name='$Lang::tr{'edit'}' src='/images/edit.gif' alt='$Lang::tr{'edit'}' title='$Lang::tr{'edit'}' />
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
    <td><img src='/images/edit.gif' alt='$Lang::tr{'edit'}' /></td>
    <td class='base'>$Lang::tr{'edit'}</td>
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
	if (rindex ($settings{'SORT_NAMELIST'},'Rev') != -1) {
	    $qs=substr ($settings{'SORT_NAMELIST'},0,length($settings{'SORT_NAMELIST'})-3);
	    if ($qs eq 'NAME') {
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
	    $qs=$settings{'SORT_NAMELIST'};
	    if ($qs eq 'NAME') {
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

	my @record = ('KEY',$key++,'EN',$temp[0],'NAME',$temp[1],'EXTIP',$temp[2],'PORT',$temp[3],'PROTO',$temp[4],'SEL',$temp[5],'MODE',$temp[6],'ENDPOINTS',$temp[7],'EPORT',$temp[8],'MONITOR',$temp[9]);
	my $record = {};                        	# create a reference to empty hash
	%{$record} = @record;                		# populate that hash with @record
	$entries{$record->{KEY}} = $record; 		# add this to a hash of hashes
    }

    open(FILE, ">$datafile") or die 'routing datafile error';

    # Each field value is printed , with the newline ! Don't forget separator and order of them.
    foreach my $entry (sort fixedleasesort keys %entries) {
	print FILE "$entries{$entry}->{EN},$entries{$entry}->{NAME},$entries{$entry}->{EXTIP},$entries{$entry}->{PORT},$entries{$entry}->{PROTO},$entries{$entry}->{SEL},$entries{$entry}->{MODE},$entries{$entry}->{ENDPOINTS},$entries{$entry}->{EPORT},$entries{$entry}->{MONITOR}\n";
    }

    close(FILE);
    # Reload sorted  @current
    open (FILE, "$datafile");
    @current = <FILE>;
    close (FILE);
}

#
# Build the configuration file
#
sub CreateLB {
	my (%settings) = @_;
	my $sel;
	my $mode;
	my @loxicmd_options;
	my $command = 'loxicmd';
	my $name = "--name=" . "$settings{'NAME'}";
	my $proto = "--" . "$settings{'PROTO'}" . "=" . "$settings{'PORT'}" . ":" . "$settings{'EPORT'}";

	if ($settings{'SEL'}) {
		$sel = "--select=" . "$settings{'SEL'}";
	}
	if ($settings{'MODE'}) {
		$mode = "--mode=" . "$settings{'MODE'}";
	}
	my $tmp = $settings{'ENDPOINTS'};
	$tmp =~ s/\|/,/g;
	my $endpoints = "--endpoints=$tmp";
	push(@loxicmd_options, "create", "lb");
	push(@loxicmd_options, "$settings{'EXTIP'}");
	push(@loxicmd_options, "$name");
	push(@loxicmd_options, "$proto");
	if ($sel) {
		push(@loxicmd_options, "$sel");
	}
	if ($mode) {
		push(@loxicmd_options, "$mode");
	}
	push(@loxicmd_options, "$endpoints");
	if ($settings{'MONITOR'} eq 'on') {
		push(@loxicmd_options, "--monitor");
	}
	&General::system($command, @loxicmd_options);
}

sub DeleteLB {
	my (%settings) = @_;
	my @loxicmd_options;
	my $command = 'loxicmd';
	my $name = "--name=" . "$settings{'NAME'}";
	push(@loxicmd_options, "delete", "lb");
	push(@loxicmd_options, "$name");
	&General::system($command, @loxicmd_options);
}
