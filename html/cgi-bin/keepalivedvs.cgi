#!/usr/bin/perl
###############################################################################
#                                                                             #
# IPFire.org - A linux based firewall                                         #
# Copyright (C) 2013 Alexander Marx <amarx@ipfire.org>                        #
# Copyright (C) 2024 BPFire                                                   #
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
#use warnings;

use Sort::Naturally;
use CGI::Carp 'fatalsToBrowser';
no warnings 'uninitialized';
require '/var/ipfire/general-functions.pl';
require '/var/ipfire/network-functions.pl';
require "/var/ipfire/location-functions.pl";
require "/usr/lib/firewall/firewall-lib.pl";
require "${General::swroot}/lang.pl";
require "${General::swroot}/header.pl";

my %hasettings=();
my %virtualserver=();
my %realserver=();
my %icmptypes=();
my %color=();
my %defaultNetworks=();
my %mainsettings=();
my %ownnet=();
my %fwfwd=();
my %fwinp=();
my %fwout=();
my %netsettings=();
my %optionsfw=();

my $errormessage;
my $hint;
my $update=0;
my $configvs		= "${General::swroot}/keepalived/configvs";
my $configrs		= "${General::swroot}/keepalived/configrs";
my $fwoptions 		= "${General::swroot}/optionsfw/settings";

unless (-e $configvs)    { &General::system("touch", "$configvs"); }
unless (-e $configrs)   { &General::system("touch", "$configrs"); }

&General::readhash("${General::swroot}/main/settings", \%mainsettings);
&General::readhash("/srv/web/ipfire/html/themes/ipfire/include/colors.txt", \%color);
&General::readhash("${General::swroot}/ethernet/settings", \%ownnet);
&General::readhash("/var/ipfire/ethernet/settings", \%netsettings);
&General::readhash($fwoptions, \%optionsfw);

&Header::getcgihash(\%hasettings);
&Header::showhttpheaders();
&Header::openpage($Lang::tr{'fwhost menu'}, 1, '');
&Header::openbigbox('100%', 'center');

#### JAVA SCRIPT ####
print<<END;
<script>
	var PROTOCOLS_WITH_PORTS = ["TCP", "UDP"];
	var update_protocol = function() {
		var protocol = \$("#protocol").val();

		if (protocol === undefined)
			return;

		// Check if we are dealing with a protocol, that knows ports.
		if (\$.inArray(protocol, PROTOCOLS_WITH_PORTS) >= 0) {
			\$("#PORT").show();
			\$("#PROTOKOLL").hide();
		} else {
			\$("#PORT").hide();
			\$("#PROTOKOLL").show();
		}
	};

	\$(document).ready(function() {
		var protocol = \$("#protocol").val();
		\$("#protocol").change(update_protocol);
		update_protocol();
		// Automatically select radio buttons when corresponding
		// dropdown menu changes.
		\$("select").change(function() {
			var id = \$(this).attr("name");
			\$('#' + id).prop("checked", true);
		});
	});
</script>
END

## ACTION ####
# Update
if ($hasettings{'ACTION'} eq 'updatevs' )
{
	&General::readhasharray("$configvs", \%virtualserver);
	foreach my $key (keys %virtualserver)
	{
		if($virtualserver{$key}[0] eq $hasettings{'orgname'})
		{
			$hasettings{'orgname'} 		= $virtualserver{$key}[0];
			$hasettings{'orgip'} 		= $virtualserver{$key}[1];
			$hasettings{'orgsub'} 		= $virtualserver{$key}[2];
			$hasettings{'netremark'}	= $virtualserver{$key}[3];
			$hasettings{'count'} 		= $virtualserver{$key}[4];
			delete $virtualserver{$key};

		}
	}
	&General::writehasharray("$configvs", \%virtualserver);
	$hasettings{'actualize'} = 'on';
	$hasettings{'ACTION'} = 'savevs';
}
if ($hasettings{'ACTION'} eq 'updaters')
{
	my ($ip,$subnet);
	&General::readhasharray("$configrs", \%realserver);
	foreach my $key (keys %realserver)
	{
		if($realserver{$key}[0] eq $hasettings{'orgname'})
		{
			if ($realserver{$key}[1] eq 'ip'){
				($ip,$subnet) = split (/\//,$realserver{$key}[2]);
			}else{
				$ip = $realserver{$key}[2];
			}
			$hasettings{'orgip'} = $ip;
			delete $realserver{$key};
			&General::writehasharray("$configrs", \%realserver);
		}
	}
	$hasettings{'actualize'} = 'on';
	if($hasettings{'orgip'}){
	$hasettings{'ACTION'} = 'savers';
	}else{
		$hasettings{'ACTION'} = $Lang::tr{'fwhost newhost'};
	}
}
# save
if ($hasettings{'ACTION'} eq 'savevs' )
{
	my $needrules=0;
	if ($hasettings{'orgname'} eq ''){$hasettings{'orgname'}=$hasettings{'HOSTNAME'};}
	#check if all fields are set
	if ($hasettings{'HOSTNAME'} eq '' || $hasettings{'IP'} eq '' || $hasettings{'SUBNET'} eq '')
	{
		$errormessage=$errormessage.$Lang::tr{'fwhost err empty'};
		&addvs;
		&viewtablevs;
	}else{
		#convert ip if leading '0' exists
		$hasettings{'IP'} = &Network::ip_remove_zero($hasettings{'IP'});

		#check valid ip
		if (!&General::validipandmask($hasettings{'IP'}."/".$hasettings{'SUBNET'}))
		{
			$errormessage=$errormessage.$Lang::tr{'fwhost err addr'};
			$hasettings{'BLK_HOST'}	='readonly';
			$hasettings{'NOCHECK'}	='false';
			$hasettings{'error'}	='on';
		}
		#check remark
		if ($hasettings{'NETREMARK'} ne '' && !&validremark($hasettings{'NETREMARK'})){
			$errormessage=$Lang::tr{'fwhost err remark'};
			$hasettings{'error'}	='on';
		}
		#check if subnet is sigle host
		if(&General::iporsubtocidr($hasettings{'SUBNET'}) eq '32')
		{
			$errormessage=$errormessage.$Lang::tr{'fwhost err sub32'};
		}
		if($hasettings{'error'} ne 'on'){
				my $fullip="$hasettings{'IP'}/".&General::iporsubtocidr($hasettings{'SUBNET'});
				$errormessage=$errormessage.&General::checksubnets($hasettings{'HOSTNAME'},$fullip,"","exact");
		}
		#only check plausi when no error till now
		if (!$errormessage){
			&plausicheck("editvs");
		}
		if($hasettings{'actualize'} eq 'on' && $hasettings{'newnet'} ne 'on' && $errormessage)
		{
			$hasettings{'actualize'} = '';
			my $key = &General::findhasharraykey (\%virtualserver);
			foreach my $i (0 .. 3) { $virtualserver{$key}[$i] = "";}
			$virtualserver{$key}[0] = $hasettings{'orgname'} ;
			$virtualserver{$key}[1] = $hasettings{'orgip'} ;
			$virtualserver{$key}[2] = $hasettings{'orgsub'};
			$virtualserver{$key}[3] = $hasettings{'orgnetremark'};
			&General::writehasharray("$configvs", \%virtualserver);
			undef %virtualserver;
		}
		if (!$errormessage){
			&General::readhasharray("$configvs", \%virtualserver);
			if ($hasettings{'ACTION'} eq 'updatevs'){
				if ($hasettings{'update'} == '0'){
					foreach my $key (keys %virtualserver) {
						if($virtualserver{$key}[0] eq $hasettings{'orgname'}){
							delete $virtualserver{$key};
							last;
						}
					}
				}
			}
			#get count if actualize is 'on'
			if($hasettings{'actualize'} eq 'on'){
				$hasettings{'actualize'} = '';
				#check if we need to reload rules
				if($hasettings{'orgip'}  ne $hasettings{'IP'}){
					$needrules='on';
				}
				if ($hasettings{'orgname'} ne $hasettings{'HOSTNAME'}){
				}
			}
			my $key = &General::findhasharraykey (\%virtualserver);
			foreach my $i (0 .. 3) { $virtualserver{$key}[$i] = "";}
			$hasettings{'SUBNET'}	= &General::iporsubtocidr($hasettings{'SUBNET'});
			$virtualserver{$key}[0] 	= $hasettings{'HOSTNAME'};
			$virtualserver{$key}[1] 	= &General::getnetworkip($hasettings{'IP'},$hasettings{'SUBNET'}) ;
			$virtualserver{$key}[2] 	= &General::iporsubtodec($hasettings{'SUBNET'}) ;
			$virtualserver{$key}[3] 	= $hasettings{'NETREMARK'};
			&General::writehasharray("$configvs", \%virtualserver);
			$hasettings{'IP'}=$hasettings{'IP'}."/".&General::iporsubtodec($hasettings{'SUBNET'});
			undef %virtualserver;
			$hasettings{'HOSTNAME'}='';
			$hasettings{'IP'}='';
			$hasettings{'SUBNET'}='';
			$hasettings{'NETREMARK'}='';
			#check if an edited net affected groups and need to reload rules
			if ($needrules eq 'on'){
				&General::firewall_config_changed();
			}
			&addvs;
			&viewtablevs;
		}else{
			$hasettings{'HOSTNAME'} = $hasettings{'orgname'};
			&addvs;
			&viewtablevs;
		}
	}
}
if ($hasettings{'ACTION'} eq 'savers')
{
	my $needrules=0;
	if ($hasettings{'orgname'} eq ''){$hasettings{'orgname'}=$hasettings{'HOSTNAME'};}
	$hasettings{'SUBNET'}='32';
	#check if all fields are set
	if ($hasettings{'HOSTNAME'} eq '' || $hasettings{'IP'} eq '' || $hasettings{'SUBNET'} eq '')
	{
		$errormessage=$errormessage.$Lang::tr{'fwhost err empty'};
		$hasettings{'ACTION'} = 'editrs';
	}else{
		if($hasettings{'IP'}=~/^([0-9a-fA-F]{1,2}:){5}[0-9a-fA-F]{1,2}$/){
			$hasettings{'type'} = 'mac';
		}elsif($hasettings{'IP'}=~/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/){
			$hasettings{'type'} = 'ip';
		}else{
			$hasettings{'type'} = '';
			$errormessage=$Lang::tr{'fwhost err ipmac'};
		}
		#check remark
		if ($hasettings{'HOSTREMARK'} ne '' && !&validremark($hasettings{'HOSTREMARK'})){
			$errormessage=$Lang::tr{'fwhost err remark'};
		}
		#CHECK IP-PART
		if ($hasettings{'type'} eq 'ip'){
			#convert ip if leading '0' exists
			$hasettings{'IP'} = &Network::ip_remove_zero($hasettings{'IP'});

			#check for subnet
			if (rindex($hasettings{'IP'},'/') eq '-1' ){
				if($hasettings{'type'} eq 'ip' && !&General::validipandmask($hasettings{'IP'}."/32"))
					{
						$errormessage.=$errormessage.$Lang::tr{'fwhost err ip'};
						$hasettings{'error'}='on';
					}
			}elsif(rindex($hasettings{'IP'},'/') ne '-1' ){
				$errormessage=$errormessage.$Lang::tr{'fwhost err ipwithsub'};
				$hasettings{'error'}='on';
			}
			#check if net or broadcast
			my @tmp= split (/\./,$hasettings{'IP'});
			if (($tmp[3] eq "0") || ($tmp[3] eq "255")){
				$errormessage=$Lang::tr{'fwhost err hostip'};
			}
		}
		#only check plausi when no error till now
		if (!$errormessage){
			&plausicheck("editrs");
		}
		if($hasettings{'actualize'} eq 'on' && $hasettings{'newrs'} ne 'on' && $errormessage){
			$hasettings{'actualize'} = '';
			my $key = &General::findhasharraykey (\%realserver);
			foreach my $i (0 .. 3) { $realserver{$key}[$i] = "";}
			$realserver{$key}[0] = $hasettings{'orgname'} ;
			$realserver{$key}[1] = $hasettings{'type'} ;
			if($realserver{$key}[1] eq 'ip'){
				$realserver{$key}[2] = $hasettings{'orgip'}."/".&General::iporsubtodec($hasettings{'SUBNET'});
			}else{
				$realserver{$key}[2] = $hasettings{'orgip'};
			}
			$realserver{$key}[3] = $hasettings{'orgremark'};
			&General::writehasharray("$configrs", \%realserver);
			undef %realserver;
		}
		if (!$errormessage){
			#get count if host was edited
			if($hasettings{'actualize'} eq 'on'){
				if($hasettings{'orgip'} ne $hasettings{'IP'}){
					$needrules='on';
				}
				if($hasettings{'orgname'} ne $hasettings{'HOSTNAME'}){
					#check if we need to update firewallrules
				}
			}
			my $key = &General::findhasharraykey (\%realserver);
			foreach my $i (0 .. 3) { $realserver{$key}[$i] = "";}
			$realserver{$key}[0] = $hasettings{'HOSTNAME'} ;
			$realserver{$key}[1] = $hasettings{'type'} ;
			if ($hasettings{'type'} eq 'ip'){
				$realserver{$key}[2] = $hasettings{'IP'}."/".&General::iporsubtodec($hasettings{'SUBNET'});
			}else{
				$realserver{$key}[2] = $hasettings{'IP'};
			}
			$realserver{$key}[3] = $hasettings{'HOSTREMARK'};
			&General::writehasharray("$configrs", \%realserver);
			undef %realserver;
			$hasettings{'HOSTNAME'}='';
			$hasettings{'IP'}='';
			$hasettings{'type'}='';
			 $hasettings{'HOSTREMARK'}='';
			#check if we need to update rules while host was edited
			if($needrules eq 'on'){
				&General::firewall_config_changed();
			}
			&addrs;
			&viewtablers;
		}else{
			&addrs;
			&viewtablers;
		}
	}
}
# edit
if ($hasettings{'ACTION'} eq 'editvs')
{
	&addvs;
	&viewtablevs;
}
if ($hasettings{'ACTION'} eq 'editrs')
{
	&addrs;
	&viewtablers;
}
# reset
if ($hasettings{'ACTION'} eq 'resetvs')
{
	$hasettings{'HOSTNAME'} ="";
	$hasettings{'IP'} 		="";
	$hasettings{'SUBNET'}	="";
	&showmenu;
}
if ($hasettings{'ACTION'} eq 'resetrs')
{
	$hasettings{'HOSTNAME'} ="";
	$hasettings{'IP'} 		="";
	$hasettings{'type'} 	="";
	&showmenu;
}
# delete
if ($hasettings{'ACTION'} eq 'delnet')
{
	&General::readhasharray("$configvs", \%virtualserver);
	foreach my $key (keys %virtualserver) {
		if($hasettings{'key'} eq $virtualserver{$key}[0]){
			delete $virtualserver{$key};
			&General::writehasharray("$configvs", \%virtualserver);
			last;
		}
	}
	&addvs;
	&viewtablevs;
}
if ($hasettings{'ACTION'} eq 'delhost')
{
	&General::readhasharray("$configrs", \%realserver);
	foreach my $key (keys %realserver) {
		if($hasettings{'key'} eq $realserver{$key}[0]){
			delete $realserver{$key};
			&General::writehasharray("$configrs", \%realserver);
			last;
		}
	}
	&addrs;
	&viewtablers;
}
if ($hasettings{'ACTION'} eq $Lang::tr{'fwhost newnet'})
{
	&addvs;
	&viewtablevs;
}
if ($hasettings{'ACTION'} eq $Lang::tr{'fwhost newhost'})
{
	&addrs;
	&viewtablers;
}
###  VIEW  ###
if($hasettings{'ACTION'} eq '')
{
	&showmenu;
}
###  FUNCTIONS  ###
sub showmenu {
	&Header::openbox('100%', 'left',);
	print "$Lang::tr{'fwhost welcome'}";
	print<<END;
	<br><br><table border='0' width='100%'>
	<tr><td><form method='post'><input type='submit' name='ACTION' value='$Lang::tr{'fwhost newnet'}' ><input type='submit' name='ACTION' value='$Lang::tr{'fwhost newhost'}' ><input type='submit' name='ACTION' value='$Lang::tr{'fwhost newgrp'}' ><input type='submit' name='ACTION' value='$Lang::tr{'fwhost newlocationgrp'}' ></form></td>
	<td align='right'><form method='post'><input type='submit' name='ACTION' value='$Lang::tr{'fwhost newservice'}' ><input type='submit' name='ACTION' value='$Lang::tr{'fwhost newservicegrp'}' ></form></td></tr>
	<tr><td colspan='6'></td></tr></table>
END
	&Header::closebox();

}
# Add
sub addvs {
    &error;
    &showmenu;
    &Header::openbox('100%', 'left', $Lang::tr{'fwhost addnet'});
    $hasettings{'orgname'} = $hasettings{'HOSTNAME'};
    $hasettings{'orgnetremark'} = $hasettings{'NETREMARK'};

    print <<END;
<table border='0' width='100%'>
<tr>
    <td width='15%'>$Lang::tr{'name'}:</td>
    <td>
        <form method='post'>
            <input type='TEXT' name='HOSTNAME' id='textbox1' value='$hasettings{'HOSTNAME'}' $hasettings{'BLK_HOST'} size='20'>
            <script>document.getElementById('textbox1').focus()</script>
    </td>
</tr>
<tr>
    <td>$Lang::tr{'fwhost netaddress'}:</td>
    <td><input type='TEXT' name='IP' value='$hasettings{'IP'}' $hasettings{'BLK_IP'} size='20' maxlength='15'></td>
</tr>
<tr>
    <td>$Lang::tr{'netmask'}:</td>
    <td><input type='TEXT' name='SUBNET' value='$hasettings{'SUBNET'}' $hasettings{'BLK_IP'} size='20' maxlength='15'></td>
</tr>
<tr>
    <td>$Lang::tr{'remark'}:</td>
    <td><input type='TEXT' name='NETREMARK' value='$hasettings{'NETREMARK'}' style='width: 98.5%;'></td>
</tr>
<tr>
    <td colspan='6'><br></td>
</tr>
<tr>
END

    if ($hasettings{'ACTION'} eq 'editvs' || $hasettings{'error'} eq 'on') {
        print <<END;
    <td colspan='6' align='right'>
        <input type='submit' value='$Lang::tr{'update'}' style='min-width:100px;'>
        <input type='hidden' name='ACTION' value='updatevs'>
        <input type='hidden' name='orgnetremark' value='$hasettings{'orgnetremark'}'>
        <input type='hidden' name='orgname' value='$hasettings{'orgname'}'>
        <input type='hidden' name='update' value='on'>
        <input type='hidden' name='newnet' value='$hasettings{'newnet'}'>
    </td>
</form>
END
    } else {
        print <<END;
    <td colspan='6' align='right'>
        <input type='submit' value='$Lang::tr{'save'}' style='min-width:100px;'>
        <input type='hidden' name='ACTION' value='savevs'>
        <input type='hidden' name='newnet' value='on'>
    </td>
</form>
END
    }
    
    print <<END;
<form method='post' style='display:inline'>
    <input type='submit' value='$Lang::tr{'fwhost back'}' style='min-width:100px;'>
    <input type='hidden' name='ACTION' value='resetvs'>
</form>
</td>
</tr>
</table>
END

    &Header::closebox();
}

sub addrs {
    &error;
    &showmenu;
    &Header::openbox('100%', 'left', $Lang::tr{'fwhost addhost'});

    $hasettings{'orgname'} = $hasettings{'HOSTNAME'};
    $hasettings{'orgremark'} = $hasettings{'HOSTREMARK'};

    print <<END;
<table width='100%'>
<tr>
    <td>$Lang::tr{'name'}:</td>
    <td>
        <form method='post' style='display:inline;'>
        <input type='TEXT' name='HOSTNAME' id='textbox1' value='$hasettings{'HOSTNAME'}' $hasettings{'BLK_HOST'} size='20'>
        <script>document.getElementById('textbox1').focus()</script>
    </td>
</tr>
<tr>
    <td>IP/MAC:</td>
    <td><input type='TEXT' name='IP' value='$hasettings{'IP'}' $hasettings{'BLK_IP'} size='20' maxlength='17'></td>
</tr>
<tr>
    <td width='10%'>$Lang::tr{'remark'}:</td>
    <td><input type='TEXT' name='HOSTREMARK' value='$hasettings{'HOSTREMARK'}' style='width:98%;'></td>
</tr>
<tr>
    <td colspan='5'><br></td>
</tr>
<tr>
END

    if ($hasettings{'ACTION'} eq 'editrs' || $hasettings{'error'} eq 'on') {
        print <<END;
    <td colspan='4' align='right'>
        <input type='submit' value='$Lang::tr{'update'}' style='min-width:100px;'/>
        <input type='hidden' name='ACTION' value='updaters'>
        <input type='hidden' name='orgremark' value='$hasettings{'orgremark'}'>
        <input type='hidden' name='orgname' value='$hasettings{'orgname'}'>
        <input type='hidden' name='update' value='on'>
        <input type='hidden' name='newrs' value='$hasettings{'newrs'}'>
        </form>
END
    } else {
        print <<END;
    <td colspan='4' align='right'>
        <input type='submit' name='savers' value='$Lang::tr{'save'}' style='min-width:100px;'/>
        <input type='hidden' name='ACTION' value='savers'/>
        <input type='hidden' name='newrs' value='on'>
        </form>
END
    }

    print <<END;
    <form method='post' style='display:inline'>
    <input type='submit' value='$Lang::tr{'fwhost back'}' style='min-width:100px;'/>
    <input type='hidden' name='ACTION' value='resetrs'>
    </form></td>
</tr>
</table>
END

    &Header::closebox();
}

# View

sub viewtablers {
    if (!-z $configrs) {
        &Header::openbox('100%', 'left', $Lang::tr{'fwhost cust addr'});
        &General::readhasharray("$configrs", \%realserver);

        if (!keys %realserver) {
            print "<center><b>$Lang::tr{'fwhost empty'}</b>";
        } else {
            print <<END;
<table width='100%' cellspacing='0' class='tbl'>
<tr>
    <th align='center'><b>$Lang::tr{'name'}</b></th>
    <th align='center'><b>$Lang::tr{'fwhost ip_mac'}</b></th>
    <th align='center'><b>$Lang::tr{'remark'}</b></th>
    <th></th>
    <th width='3%'></th>
</tr>
END
        }

        my $count = 0;
        my $col = '';

        foreach my $key (sort { ncmp($realserver{$a}[0], $realserver{$b}[0]) } keys %realserver) {
            if (($hasettings{'ACTION'} eq 'editrs' || $hasettings{'error'}) && $hasettings{'HOSTNAME'} eq $realserver{$key}[0]) {
                print "<tr>";
                $col = "bgcolor='${Header::colouryellow}'";
            } elsif ($count % 2) {
                print "<tr>";
                $col = "bgcolor='$color{'color20'}'";
            } else {
                $col = "bgcolor='$color{'color22'}'";
                print "<tr>";
            }

            my ($ip, $sub) = split(/\//, $realserver{$key}[2]);
            
            print "<td width='20%' align='center' $col>$realserver{$key}[0]</td>";
            print "<td width='20%' align='center' $col>" . &getcolor($ip) . "</td>";
            print "<td width='50%' align='center' $col>$realserver{$key}[3]</td>";
            
            print <<END;
<td width='1%' $col>
    <form method='post'>
        <input type='image' src='/images/edit.gif' align='middle' alt='$Lang::tr{'edit'}' title='$Lang::tr{'edit'}' />
        <input type='hidden' name='ACTION' value='editrs' />
        <input type='hidden' name='HOSTNAME' value='$realserver{$key}[0]' />
        <input type='hidden' name='IP' value='$ip' />
        <input type='hidden' name='type' value='$realserver{$key}[1]' />
        <input type='hidden' name='HOSTREMARK' value='$realserver{$key}[3]' />
    </form>
</td>
END

                print "<td width='1%' $col><form method='post'>";
                print "<input type='image' src='/images/delete.gif' align='middle' alt='$Lang::tr{'delete'}' title='$Lang::tr{'delete'}' />";
                print "<input type='hidden' name='ACTION' value='delhost' />";
                print "<input type='hidden' name='key' value='$realserver{$key}[0]' />";
                print "</form></td></tr>";

            $count++;
        }

        print "</table>";
        &Header::closebox();
    }
}

sub viewtablevs {
    if (!-z $configvs) {
        &Header::openbox('100%', 'left', $Lang::tr{'fwhost cust net'});
        &General::readhasharray("$configvs", \%virtualserver);

        if (!keys %virtualserver) {
            print "<center><b>$Lang::tr{'fwhost empty'}</b>";
        } else {
            print <<END;
<table width='100%' cellspacing='0' class='tbl'>
<tr>
    <th align='center'><b>$Lang::tr{'name'}</b></th>
    <th align='center'><b>$Lang::tr{'fwhost netaddress'}</b></th>
    <th align='center'><b>$Lang::tr{'remark'}</b></th>
    <th></th>
    <th width='3%'></th>
</tr>
END
        }

        my $count = 0;
        my $col = '';

        foreach my $key (sort { ncmp($a, $b) } keys %virtualserver) {
            if ($hasettings{'ACTION'} eq 'editvs' && $hasettings{'HOSTNAME'} eq $virtualserver{$key}[0]) {
                print " <tr>";
                $col = "bgcolor='${Header::colouryellow}'";
            } elsif ($count % 2) {
                $col = "bgcolor='$color{'color20'}'";
                print " <tr>";
            } else {
                $col = "bgcolor='$color{'color22'}'";
                print " <tr>";
            }

            my $colnet = "$virtualserver{$key}[1]/" . &General::subtocidr($virtualserver{$key}[2]);

            print "<td width='20%' align='center' $col><form method='post'>$virtualserver{$key}[0]</td>";
            print "<td width='15%' align='center' $col>" . &getcolor($colnet) . "</td>";
            print "<td width='40%' align='center' $col>$virtualserver{$key}[3]</td>";

            print <<END;
<td width='1%' $col>
    <input type='image' src='/images/edit.gif' align='middle' alt='$Lang::tr{'edit'}' title='$Lang::tr{'edit'}' />
    <input type='hidden' name='ACTION' value='editvs' />
    <input type='hidden' name='HOSTNAME' value='$virtualserver{$key}[0]' />
    <input type='hidden' name='IP' value='$virtualserver{$key}[1]' />
    <input type='hidden' name='SUBNET' value='$virtualserver{$key}[2]' />
    <input type='hidden' name='NETREMARK' value='$virtualserver{$key}[3]' />
</td></form>
END

            print "<td width='1%' $col><form method='post'>";
            print "<input type='image' src='/images/delete.gif' align='middle' alt='$Lang::tr{'delete'}' title='$Lang::tr{'delete'}' />";
            print "<input type='hidden' name='ACTION' value='delnet' />";
            print "<input type='hidden' name='key' value='$virtualserver{$key}[0]' />";
            print "</form></td></tr>";

            $count++;
        }

        print "</table>";
        &Header::closebox();
    }
}

sub getcolor
{
		my $c=shift;
		my $sip;
		my $scidr;
		my $tdcolor='';
		#Check if MAC
		if (&General::validmac($c)){ return $c;}

		#Check if we got a full IP with subnet then split it
		if($c =~ /^(.*?)\/(.*?)$/){
			($sip,$scidr) = split ("/",$c);
		}else{
			$sip=$c;
		}

		#Now check if IP is part of ORANGE,BLUE or GREEN
		if ( &Header::orange_used() && &General::IpInSubnet($sip,$netsettings{'ORANGE_ADDRESS'},$netsettings{'ORANGE_NETMASK'})){
			$tdcolor="<font style='color: $Header::colourorange;'>$c</font>";
			return $tdcolor;
		}
		if ( &General::IpInSubnet($sip,$netsettings{'GREEN_ADDRESS'},$netsettings{'GREEN_NETMASK'})){
			$tdcolor="<font style='color: $Header::colourgreen;'>$c</font>";
			return $tdcolor;
		}
		if ( &Header::blue_used() && &General::IpInSubnet($sip,$netsettings{'BLUE_ADDRESS'},$netsettings{'BLUE_NETMASK'})){
			$tdcolor="<font style='color: $Header::colourblue;'>$c</font>";
			return $tdcolor;
		}
		if ("$sip/$scidr" eq "0.0.0.0/0"){
			$tdcolor="<font style='color: $Header::colourred;'>$c</font>";
			return $tdcolor;
		}

		return "$c";
}


sub checkname
{
	my %hash=%{(shift)};
	foreach my $key (keys %hash) {
		if($hash{$key}[0] eq $hasettings{'HOSTNAME'}){
			return 0;
		}
	}
	return 1;

}
sub checkip
{

	my %hash=%{(shift)};
	my $a=shift;
	foreach my $key (keys %hash) {
		if($hash{$key}[$a] eq $hasettings{'IP'}."/".&General::iporsubtodec($hasettings{'SUBNET'})){
			return 0;
		}
	}
	return 1;
}
sub error
{
	if ($errormessage) {
		&Header::openbox('100%', 'left', $Lang::tr{'error messages'});
		print "<class name='base'>$errormessage\n";
		print "&nbsp;</class>\n";
		&Header::closebox();
	}
}
sub hint
{
	if ($hint) {
		&Header::openbox('100%', 'left', $Lang::tr{'fwhost hint'});
		print "<class name='base'>$hint\n";
		print "&nbsp;</class>\n";
		&Header::closebox();
	}
}
sub get_name
{
	my $val=shift;
	&General::setup_default_networks(\%defaultNetworks);
	foreach my $network (sort keys %defaultNetworks)
	{
		return "$network" if ($val eq $defaultNetworks{$network}{'NAME'});
	}
}
sub gethostcount
{
        my $searchstring=shift;
}
sub getnetcount
{
	my $searchstring=shift;
}
sub plausicheck
{
	my $edit=shift;
	#check hostname
	if (!&validhostname($hasettings{'HOSTNAME'}))
	{
		$errormessage=$errormessage.$Lang::tr{'fwhost err name'};
		$hasettings{'BLK_IP'}='readonly';
		$hasettings{'HOSTNAME'} = $hasettings{'orgname'};
		if ($hasettings{'update'} eq 'on'){$hasettings{'ACTION'}=$edit;}
	}
	#check if network with this name already exists
	&General::readhasharray("$configvs", \%virtualserver);
	if (!&checkname(\%virtualserver))
	{
		$errormessage=$errormessage."<br>".$Lang::tr{'fwhost err netexist'};
		$hasettings{'HOSTNAME'} = $hasettings{'orgname'};
		if ($hasettings{'update'} eq 'on'){$hasettings{'ACTION'}=$edit;}
	}
	#check if network ip already exists
	if (!&checkip(\%virtualserver,1))
	{
		$errormessage=$errormessage."<br>".$Lang::tr{'fwhost err net'};
		if ($hasettings{'update'} eq 'on'){$hasettings{'ACTION'}=$edit;}
	}
	#check if host with this name already exists
	&General::readhasharray("$configrs", \%realserver);
	if (!&checkname(\%realserver))
	{
		$errormessage.="<br>".$Lang::tr{'fwhost err hostexist'};
		$hasettings{'HOSTNAME'} = $hasettings{'orgname'};
		if ($hasettings{'update'} eq 'on'){$hasettings{'ACTION'}=$edit;}
	}
	#check if host with this ip already exists
	if (!&checkip(\%realserver,2))
	{
		$errormessage=$errormessage."<br>".$Lang::tr{'fwhost err ipcheck'};
	}
	return;
}
sub decrease
{
	&General::readhasharray("$configvs", \%virtualserver);
	&General::readhasharray("$configrs", \%realserver);
	&General::writehasharray("$configvs", \%virtualserver);
	&General::writehasharray("$configrs", \%realserver);
}
sub validhostname
{
	# Checks a hostname against RFC1035
        my $hostname = $_[0];

	# Each part should be at least two characters in length
	# but no more than 63 characters
	if (length ($hostname) < 1 || length ($hostname) > 63) {
		return 0;}
	# Only valid characters are a-z, A-Z, 0-9 and -
	if ($hostname !~ /^[a-zA-ZäöüÖÄÜ0-9-_.;()\/\s]*$/) {
		return 0;}
	# First character can only be a letter or a digit
	if (substr ($hostname, 0, 1) !~ /^[a-zA-ZöäüÖÄÜ0-9]*$/) {
		return 0;}
	# Last character can only be a letter or a digit
	if (substr ($hostname, -1, 1) !~ /^[a-zA-ZöäüÖÄÜ0-9()]*$/) {
		return 0;}
	return 1;
}
sub validremark
{
	# Checks a hostname against RFC1035
        my $remark = $_[0];
	# Each part should be at least two characters in length
	# but no more than 63 characters
	if (length ($remark) < 1 || length ($remark) > 255) {
		return 0;}
	# Only valid characters are a-z, A-Z, 0-9 and -
	if ($remark !~ /^[a-zäöüA-ZÖÄÜ0-9-.:;\|_()\/\s]*$/) {
		return 0;}
	# First character can only be a letter or a digit
	if (substr ($remark, 0, 1) !~ /^[a-zäöüA-ZÖÄÜ0-9]*$/) {
		return 0;}
	# Last character can only be a letter or a digit
	if (substr ($remark, -1, 1) !~ /^[a-zöäüA-ZÖÄÜ0-9.:;_)]*$/) {
		return 0;}
	return 1;
}
&Header::closebigbox();
&Header::closepage();
