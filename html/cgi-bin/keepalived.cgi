#!/usr/bin/perl
###############################################################################
#                                                                             #
# IPFire.org - A linux based firewall                                         #
# Copyright (C) 2007-2023  IPFire Team  <info@ipfire.org>                     #
# Copyright (C) 2024  BPFire  <vincent.mc.li@gmail.com>                       #
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
use experimental 'smartmatch';

# enable only the following on debugging purpose
#use warnings;
#use CGI::Carp 'fatalsToBrowser';

require '/var/ipfire/general-functions.pl';
require "${General::swroot}/lang.pl";
require "${General::swroot}/header.pl";
#workaround to suppress a warning when a variable is used only once
my @dummy = ( ${Header::colouryellow} );
undef (@dummy);

our %hasettings=();
our %netsettings=();
my %mainsettings=();
my %timesettings=();
my $setting = "${General::swroot}/keepalived/settings";
my $runsetting = "${General::swroot}/keepalived/runsettings";
my $loxilbipfile = "${General::swroot}/loxilb/ipconfigfile";
									# because we need commas in the some data
my $errormessage = '';
#remove 'ENABLE_HA' from '/var/ipfire/keepalived/settings' as it could affect keepalived running state
my @nosaved=('ENABLE_HA');
my %color = ();

$hasettings{'ENABLE_HA'} = 'off';

# Load multiline data
our @current = ();
if (open(FILE, "$loxilbipfile")) {
    @current = <FILE>;
    close (FILE);
}

&Header::showhttpheaders();
our @ITFs=('RED', 'GREEN');
my @STATE= ('MASTER', 'BACKUP');

#Settings1 for the first screen box
foreach my $itf (@ITFs) {
    $hasettings{"ENABLE_${itf}"} = 'off';
    $hasettings{"state_${itf}"} = '';
    $hasettings{"garp_master_delay_${itf}"} = '';
    $hasettings{"virtual_router_id_${itf}"} = '';
    $hasettings{"priority_${itf}"} = '';
    $hasettings{"advert_int_${itf}"} = '';
    $hasettings{"auth_pass_${itf}"} = '';
    $hasettings{"unicast_peer_${itf}"} = '';
    $hasettings{"virtual_ipaddress_${itf}"} = '';
}

# Read Ipcop settings
&General::readhash("${General::swroot}/ethernet/settings", \%netsettings);
&General::readhash("${General::swroot}/main/settings", \%mainsettings);
&General::readhash("/srv/web/ipfire/html/themes/ipfire/include/colors.txt", \%color);

#Get GUI values
&Header::getcgihash(\%hasettings);

if ($hasettings{'ACTION'} eq $Lang::tr{'enable'})
{
	#remove @nosaved from $hasettings before writehash to 'runsettings' file since 'runsetting' is only for keepalived running state
	foreach my $itf (@ITFs) {
		my @nosaved = ("virtual_router_id_${itf}", "priority_${itf}", "unicast_peer_${itf}", "auth_pass_${itf}", "garp_master_delay_${itf}", "advert_int_${itf}", "virtual_ipaddress_${itf}", "state_${itf}", "ENABLE_${itf}");
		map (delete ($hasettings{$_}) ,(@nosaved));
	}
        &General::writehash("$runsetting", \%hasettings);
        if ($hasettings{'ENABLE_HA'} eq 'on') {
                &General::system('/usr/bin/touch', "${General::swroot}/keepalived/enable_ha");
                &General::system('/usr/local/bin/keepalivedctrl', 'start');
        } else {
                &General::system('/usr/local/bin/keepalivedctrl', 'stop');
                unlink "${General::swroot}/keepalived/enable_ha";
        }
}

# Check Settings1 first because they are needed by &buildconf
if ($hasettings{'ACTION'} eq $Lang::tr{'save'}) {
    foreach my $itf (@ITFs) {
	if ($hasettings{"ENABLE_${itf}"} eq 'on' ) {

		if (!(&General::validnum($hasettings{"virtual_router_id_${itf}"})) || ($hasettings{"virtual_router_id_${itf}"} eq '')) {
		    $errormessage = "virtual_router_id" .  " is $Lang::tr{'required field'}" . " or not valid num";
		    goto ERROR;
		}
		if (!(&General::validnum($hasettings{"priority_${itf}"})) || ($hasettings{"priority_${itf}"} eq '')) {
		    $errormessage = "priority" . " is $Lang::tr{'required field'}" . " or not valid num";
		    goto ERROR;
		}
		if (!(&General::validnum($hasettings{"advert_int_${itf}"})) || ($hasettings{"advert_int_${itf}"} eq '')) {
		    $errormessage = "advert_int" . " is $Lang::tr{'required field'}" . " or not valid num";
		    goto ERROR;
		}
		if (!(&General::validnum($hasettings{"garp_master_delay_${itf}"})) || ($hasettings{"garp_master_delay_${itf}"} eq '')) {
		    $errormessage = "garp master delay" . " is $Lang::tr{'required field'}" . " or not valid num";
		    goto ERROR;
		}
	}

    }

    map (delete ($hasettings{$_}) ,@nosaved,'ACTION','KEY1','KEY2','q');	# Must not be saved
    &General::writehash($setting, \%hasettings);		# Save good settings
    $hasettings{'ACTION'} = $Lang::tr{'save'};		# create an 'ACTION'
    map ($hasettings{$_} = '',@nosaved,'KEY1','KEY2');	# and reinit vars to empty
    &buildconf;
    ERROR:
}

if ($hasettings{'ACTION'} eq '' ) { # First launch from GUI

    # Set default DHCP values only if blank and disabled
    foreach my $itf (@ITFs) {
	if ($hasettings{"ENABLE_${itf}"} ne 'on' ) {
	    $hasettings{"virtual_router_id_${itf}"} = '50';
	    $hasettings{"priority_${itf}"} = '100';
	    $hasettings{"advert_int_${itf}"} = '1';
	    $hasettings{"auth_pass_${itf}"} = '';
	    $hasettings{"unicast_peer_${itf}"} = '';
	    $hasettings{"garp_master_delay_${itf}"} = '10';
	}
    }
}

### START PAGE ###
&Header::openpage($Lang::tr{'keepalived configuration'}, 1, $Header::extraHead);
&Header::openbigbox('100%', 'left', '', $errormessage);

if ($errormessage) {
    &Header::openbox('100%', 'left', $Lang::tr{'error messages'});
    print "<font class='base' color=red>$errormessage&nbsp;</font>\n";
    &Header::closebox();
}

# Read configuration file.
&General::readhash("$runsetting", \%hasettings);

# Checkbox pre-selection.
my $checked;
if ($hasettings{'ENABLE_HA'} eq "on") {
        $checked = "checked='checked'";
}

my $sactive = "<table cellpadding='2' cellspacing='0' bgcolor='${Header::colourred}' width='50%'><tr><td align='center'><b><font color='#FFFFFF'>$Lang::tr{'stopped'}</font></b></td></tr></table>";

my @status = &General::system_output('/usr/local/bin/keepalivedctrl', 'status');

if (grep(/is running/, @status)){
        $sactive = "<table cellpadding='2' cellspacing='0' bgcolor='${Header::colourgreen}' width='50%'><tr><td align='center'><b><font color='#FFFFFF'>$Lang::tr{'running'}</font></b></td></tr></table>";
}

&Header::openbox('100%', 'center', $Lang::tr{'keepalived status'});

print <<END;
        <table width='100%'>
        <form method='POST' action='$ENV{'SCRIPT_NAME'}'>
        <td width='25%'>&nbsp;</td>
        <td width='25%'>&nbsp;</td>
        <td width='25%'>&nbsp;</td>
        <tr><td class='boldbase'>$Lang::tr{'keepalived status'}</td>
        <td align='left'>$sactive</td>
        </tr>
        <tr>
        <td width='50%' class='boldbase'>$Lang::tr{'enable'}
        <td><input type='checkbox' name='ENABLE_HA' $checked></td>
        <td align='center'><input type='submit' name='ACTION' value='$Lang::tr{'enable'}'></td>
        </tr>
END

print "</form> </table>\n";

&Header::closebox();
#


&General::readhash($setting, \%hasettings);   		# Get saved settings and reset to good if needed

&Header::openbox('100%', 'left', $Lang::tr{'keepalived config'});
print "<form method='post' action='$ENV{'SCRIPT_NAME'}'>";

foreach my $itf (@ITFs) {
    my %checked = ();
    my @vips;
    my $lc_itf = lc($itf);
    my $current_state = $hasettings{"state_${itf}"};
    my @current_vips = split(/\|/, $hasettings{"virtual_ipaddress_${itf}"}); #multi selected value is separated by pipe |

    foreach my $line (@current) {
        chomp($line);
        my @temp = split(/\,/, $line);
        if ($temp[1] eq $netsettings{"${itf}_DEV"}) {
            push(@vips, $temp[0]);
        }
    }
    $checked{'ENABLE'}{'on'} = ($hasettings{"ENABLE_${itf}"} ne 'on') ? '' : "checked='checked'";

    print <<END;
<table width='100%'>
<tr>
    <td width='25%' class='boldbase'><b><font color='$lc_itf'>$Lang::tr{"$lc_itf interface"}</font></b></td>
    <td class='base'>$Lang::tr{'enabled'}
    <input type='checkbox' name='ENABLE_${itf}' $checked{'ENABLE'}{'on'} /></td>
</tr>
<tr>
    <td class='base'>$Lang::tr{'keepalived state'}:&nbsp;</td>
    <td>
      <select name='state_${itf}' id='state' style="width: 95px;">
END

# display selected, tip from chatgpt
  foreach my $state (@STATE) {
    my $selected = ($state eq $current_state) ? 'selected' : '';
    print "<option value=\"$state\" $selected>$state</option>";
  }

print <<END;
      </select>
     </td>
</tr>

<tr>
    <td width='25%' class='base'>$Lang::tr{'keepalived virtual router id'}&nbsp;<img src='/blob.gif' alt='*' /></td>
    <td width='25%'><input type='text' name='virtual_router_id_${itf}' value='$hasettings{"virtual_router_id_${itf}"}' /></td>
</tr>
<tr>
    <td width='25%' class='base'>$Lang::tr{'keepalived priority'}&nbsp;<img src='/blob.gif' alt='*' /></td>
    <td width='25%'><input type='text' name='priority_${itf}' value='$hasettings{"priority_${itf}"}' /></td>
</tr>
<tr>
    <td width='25%' class='base'>$Lang::tr{'keepalived advert int'}&nbsp;<img src='/blob.gif' alt='*' /></td>
    <td width='25%'><input type='text' name='advert_int_${itf}' value='$hasettings{"advert_int_${itf}"}' /></td>
</tr>
<tr>
    <td width='25%' class='base'>$Lang::tr{'keepalived garp master delay'}&nbsp;</td>
    <td width='25%'><input type='text' name='garp_master_delay_${itf}' value='$hasettings{"garp_master_delay_${itf}"}' /></td>
</tr>
<tr>
    <td width='25%' class='base'>$Lang::tr{'keepalived auth pass'}&nbsp;<img src='/blob.gif' alt='*' /></td>
    <td width='25%'><input type='text' name='auth_pass_${itf}' value='$hasettings{"auth_pass_${itf}"}' /></td>
</tr>
<tr>
    <td width='25%' class='base'>$Lang::tr{'keepalived unicast peer'}&nbsp;<img src='/blob.gif' alt='*' /></td>
    <td width='25%'><input type='text' name='unicast_peer_${itf}' value='$hasettings{"unicast_peer_${itf}"}' /></td>
</tr>
<tr>
    <td class='base'>$Lang::tr{'keepalived virtual address'}:&nbsp;<img src='/blob.gif' alt='*' /></td>
    <td>
      <select name='virtual_ipaddress_${itf}' id='virtual_ipaddress' style="width: 200px;" multiple>
END

# display selected, tip from chatgpt
    foreach my $vip (@vips) {
        my $selected = (grep { $_ eq $vip } @current_vips) ? 'selected' : '';
        print "<option value=\"$vip\" $selected>$vip</option>";
    }

print <<END;

     </select>
     </td>
</tr>
</table>
<hr />
END
} # foreach itf

print <<END;
<table width='100%'>
<tr>
    <td class='base' width='25%'><img src='/blob.gif' align='top' alt='*' />&nbsp;$Lang::tr{'required field'}</td>
    <td width='40%' align='right'><input type='submit' name='ACTION' value='$Lang::tr{'save'}' /></td>
</tr>
</table>
</form>
END

&Header::closebox();

&Header::closebigbox();
&Header::closepage();

# Build the configuration file mixing  settings, fixed leases and advanced options
sub buildconf {
    open(FILE, ">/${General::swroot}/keepalived/keepalived.conf") or die "Unable to write keepalived.conf file";
    flock(FILE, 2);

    # Global settings
    print FILE "global_defs {\n";
    print FILE "\trouter_id BPFire_DEVEL\n";
    print FILE "}\n";

    print FILE "\n";

    #Subnet range definition
    foreach my $itf (@ITFs) {
	my $lc_itf=lc($itf);
	if ($hasettings{"ENABLE_${itf}"} eq 'on' ){
		print FILE "vrrp_instance VI_$lc_itf {" . "\n";
		print FILE "\tstate " . $hasettings{"state_${itf}"} . "\n";
		print FILE "\tinterface " . $netsettings{"${itf}_DEV"} . "\n";
		print FILE "\tvirtual_router_id " . $hasettings{"virtual_router_id_${itf}"} . "\n";
		print FILE "\tpriority " . $hasettings{"priority_${itf}"} . "\n";
		print FILE "\tadvert_int " . $hasettings{"advert_int_${itf}"} . "\n";
		print FILE "\tgarp_master_delay " . $hasettings{"garp_master_delay_${itf}"} . "\n";
		#unicast peer, red0 does not support multicast
		print FILE "\tunicast_peer {" . "\n";
		print FILE "\t\t" .  $hasettings{"unicast_peer_${itf}"} . "\n";
		print FILE "\t}" . "\n";
		# authentication
		print FILE "\tauthentication {" . "\n";
		print FILE "\t\tauth_type PASS" . "\n";
		print FILE "\t\tauth_pass " .  $hasettings{"auth_pass_${itf}"} . "\n";
		print FILE "\t}" . "\n";
		# virtual ipaddress
		print FILE "\tvirtual_ipaddress {" . "\n";
		my @vips = split(/\|/, $hasettings{"virtual_ipaddress_${itf}"});
		foreach my $ip (@vips) {
			print FILE "\t\t$ip" . "\n";
		}
		print FILE "\t}" . "\n";

		print FILE "} #$itf\n\n";

	    &General::system('/usr/bin/touch', "${General::swroot}/keepalived/enable_${lc_itf}");
	} else {
	    unlink "${General::swroot}/keepalived/enable_${lc_itf}";
	}
    }

    close FILE;

    &General::system_background('/usr/local/bin/keepalivedctrl', 'restart');
}
