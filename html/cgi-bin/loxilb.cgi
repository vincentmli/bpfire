#!/usr/bin/perl
###############################################################################
#                                                                             #
# IPFire.org - A linux based firewall                                         #
# Copyright (C) 2007-2020  IPFire Team  <info@ipfire.org>                     #
# Copyright (C) 2024  BPFire <vincent.mc.li@gmail.com>                     #
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
use CGI::Carp 'fatalsToBrowser';

use IO::Socket;

require '/var/ipfire/general-functions.pl';
require "${General::swroot}/location-functions.pl";
require "${General::swroot}/lang.pl";
require "${General::swroot}/header.pl";

my %color = ();
my %mainsettings = ();
my %loxilbsettings=();
my %checked=();
my $errormessage='';
my $loxilbsettingfile = "${General::swroot}/loxilb/settings";


# Read configuration file.

&General::readhash("${General::swroot}/main/settings", \%mainsettings);
&General::readhash("/srv/web/ipfire/html/themes/ipfire/include/colors.txt", \%color);

&Header::showhttpheaders();

$loxilbsettings{'ENABLE_LOXILB'} = 'off';
$loxilbsettings{'ACTION'} = '';

&Header::getcgihash(\%loxilbsettings);

if ($loxilbsettings{'ACTION'} eq $Lang::tr{'save'})
{

	&General::writehash("$loxilbsettingfile", \%loxilbsettings);

	if ($loxilbsettings{'ENABLE_LOXILB'} eq 'on') {
		&General::system('/usr/bin/touch', "${General::swroot}/loxilb/enableloxilb");
		&General::system('/usr/local/bin/loxilbctrl', 'start');
	} else {
		&General::system('/usr/local/bin/loxilbctrl', 'stop');
		unlink "${General::swroot}/loxilb/enableloxilb";
	}

}

&Header::openpage($Lang::tr{'loxilb'}, 1, '');

&Header::openbigbox('100%', 'left', '', $errormessage);

if ($errormessage) {
	&Header::openbox('100%', 'left', $Lang::tr{'error messages'});
	print "<font class='base'>$errormessage&nbsp;</font>\n";
	&Header::closebox();
}

# Read configuration file.
&General::readhash("$loxilbsettingfile", \%loxilbsettings);

# Checkbox pre-selection.
my $checked;
if ($loxilbsettings{'ENABLE_LOXILB'} eq "on") {
        $checked = "checked='checked'";
}

my $sactive = "<table cellpadding='2' cellspacing='0' bgcolor='${Header::colourred}' width='50%'><tr><td align='center'><b><font color='#FFFFFF'>$Lang::tr{'stopped'}</font></b></td></tr></table>";

my @status = &General::system_output('/usr/local/bin/loxilbctrl', 'status');

if (grep(/is running/, @status)){
        $sactive = "<table cellpadding='2' cellspacing='0' bgcolor='${Header::colourgreen}' width='50%'><tr><td align='center'><b><font color='#FFFFFF'>$Lang::tr{'running'}</font></b></td></tr></table>";
}

&Header::openbox('100%', 'center', $Lang::tr{'loxilb status'});

print <<END;
        <table width='100%'>
	<form method='POST' action='$ENV{'SCRIPT_NAME'}'>
	<td width='25%'>&nbsp;</td>
	<td width='25%'>&nbsp;</td>
	<td width='25%'>&nbsp;</td>
	<tr><td class='boldbase'>$Lang::tr{'loxilb server status'}</td>
	<td align='left'>$sactive</td>
	</tr>
	<tr>
	<td width='50%' class='boldbase'>$Lang::tr{'loxilb enable'}
	<td><input type='checkbox' name='ENABLE_LOXILB' $checked></td>
	<td align='center'><input type='submit' name='ACTION' value='$Lang::tr{'save'}'></td>
	</tr>
END

&Header::closebox();

print "</form> </table>\n";
#
&Header::closebigbox();

&Header::closepage();

