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
my $setting = "${General::swroot}/haproxy/settings";
my $configsetting = "${General::swroot}/haproxy/config";
my $loxilbipfile = "${General::swroot}/loxilb/ipconfigfile";
									# because we need commas in the some data
my $errormessage = '';
#remove 'ENABLE_HA' from '/var/ipfire/haproxy/settings' as it could affect haproxy running state
my @nosaved=('ENABLE_HAPROXY');
my %color = ();

$hasettings{'ENABLE_HAPROXY'} = 'off';

&Header::showhttpheaders();
my @MODE= ('tcp', 'http');

#Settings1 for the first screen box
$hasettings{"mode"} = '';
$hasettings{"bind"} = '';

# Read Ipcop settings
&General::readhash("${General::swroot}/ethernet/settings", \%netsettings);
&General::readhash("${General::swroot}/main/settings", \%mainsettings);
&General::readhash("/srv/web/ipfire/html/themes/ipfire/include/colors.txt", \%color);

#Get GUI values
&Header::getcgihash(\%hasettings);

if ($hasettings{'ACTION'} eq $Lang::tr{'enable'})
{
	#remove @nosaved from $hasettings before writehash to 'configsettings' file since 'configsetting' is only for haproxy running state
	my @nosaved = ("mode", "bind", "ENABLE_HAPROXY");
	map (delete ($hasettings{$_}) ,(@nosaved));
        &General::writehash("$configsetting", \%hasettings);
        if ($hasettings{'ENABLE_HAPROXY'} eq 'on') {
                &General::system('/usr/bin/touch', "${General::swroot}/haproxy/enable_ha");
                &General::system('/usr/local/bin/haproxyctrl', 'start');
        } else {
                &General::system('/usr/local/bin/haproxyctrl', 'stop');
                unlink "${General::swroot}/haproxy/enable_ha";
        }
}

# Check Settings1 first because they are needed by &buildconf
if ($hasettings{'ACTION'} eq $Lang::tr{'save'}) {

    if ($hasettings{"mode"} eq '') {
	    $errormessage = "mode" .  " is $Lang::tr{'required field'}";
	    goto ERROR;
    }
    if ($hasettings{"bind"} eq '') {
	    $errormessage = "bind" . " is $Lang::tr{'required field'}";
	    goto ERROR;
    }

    map (delete ($hasettings{$_}) ,@nosaved,'ACTION','KEY1','KEY2','q');	# Must not be saved
    &General::writehash($setting, \%hasettings);		# Save good settings
    $hasettings{'ACTION'} = $Lang::tr{'save'};		# create an 'ACTION'
    map ($hasettings{$_} = '',@nosaved,'KEY1','KEY2');	# and reinit vars to empty
    &buildconf;
    ERROR:
}

if ($hasettings{'ACTION'} eq '' ) { # First launch from GUI

    $hasettings{"mode"} = '';
    $hasettings{"bind"} = '';
}

### START PAGE ###
&Header::openpage($Lang::tr{'haproxy configuration'}, 1, $Header::extraHead);
&Header::openbigbox('100%', 'left', '', $errormessage);

if ($errormessage) {
    &Header::openbox('100%', 'left', $Lang::tr{'error messages'});
    print "<font class='base' color=red>$errormessage&nbsp;</font>\n";
    &Header::closebox();
}

# Read configuration file.
&General::readhash("$configsetting", \%hasettings);

# Checkbox pre-selection.
my $checked;
if ($hasettings{'ENABLE_HA'} eq "on") {
        $checked = "checked='checked'";
}

my $sactive = "<table cellpadding='2' cellspacing='0' bgcolor='${Header::colourred}' width='50%'><tr><td align='center'><b><font color='#FFFFFF'>$Lang::tr{'stopped'}</font></b></td></tr></table>";

my @status = &General::system_output('/usr/local/bin/haproxyctrl', 'status');

if (grep(/is running/, @status)){
        $sactive = "<table cellpadding='2' cellspacing='0' bgcolor='${Header::colourgreen}' width='50%'><tr><td align='center'><b><font color='#FFFFFF'>$Lang::tr{'running'}</font></b></td></tr></table>";
}

&Header::openbox('100%', 'center', $Lang::tr{'haproxy status'});

print <<END;
        <table width='100%'>
        <form method='POST' action='$ENV{'SCRIPT_NAME'}'>
        <td width='25%'>&nbsp;</td>
        <td width='25%'>&nbsp;</td>
        <td width='25%'>&nbsp;</td>
        <tr><td class='boldbase'>$Lang::tr{'haproxy status'}</td>
        <td align='left'>$sactive</td>
        </tr>
	<tr>
		<td colspan='4'>&nbsp;</td>
	</tr>
        <tr>
        <td width='100%' class='boldbase'>$Lang::tr{'enable'}
        <td align='left'><input type='checkbox' name='ENABLE_HA' $checked></td>
        <td align='center'><input type='submit' name='ACTION' value='$Lang::tr{'enable'}'></td>
        </tr>
END

print "</form> </table>\n";

&Header::closebox();
#


&General::readhash($setting, \%hasettings);   		# Get saved settings and reset to good if needed

&Header::openbox('100%', 'left', $Lang::tr{'haproxy config'});
print "<form method='post' action='$ENV{'SCRIPT_NAME'}'>";

my %checked = ();

print <<END;

<table width='100%'>
<tr>
    <td width='25%' class='base'>$Lang::tr{'haproxy mode'}&nbsp;<img src='/blob.gif' alt='*' /></td>
    <td width='25%'><input type='text' name='mode' value='$hasettings{"mode"}' /></td>
</tr>
<tr>
    <td width='25%' class='base'>$Lang::tr{'haproxy bind'}&nbsp;<img src='/blob.gif' alt='*' /></td>
    <td width='25%'><input type='text' name='bind' value='$hasettings{"bind"}' /></td>
</tr>

</table>
<hr />
END

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
    open(FILE, ">/${General::swroot}/haproxy/haproxy.cfg") or die "Unable to write haproxy.cfg file";
    flock(FILE, 2);

    # Global settings
    print FILE <<EOF;

global
    # to have these messages end up in /var/log/haproxy.log you will
    # need to:
    #
    # 1) configure syslog to accept network log events.  This is done
    #    by adding the '-r' option to the SYSLOGD_OPTIONS in
    #    /etc/sysconfig/syslog
    #
    # 2) configure local2 events to go to the /var/log/haproxy.log
    #   file. A line like the following can be added to
    #   /etc/sysconfig/syslog
    #
    #    local2.*                       /var/log/haproxy.log
    #
    log         127.0.0.1 local2

    chroot      /var/lib/haproxy
    pidfile     /var/run/haproxy.pid
    maxconn     4000
    user        nobody
    group       nobody
    daemon

    # turn on stats unix socket
    stats socket /var/lib/haproxy/stats

defaults
    mode                    http
    log                     global
    option                  httplog
    option                  dontlognull
    option http-server-close
    option forwardfor       except 127.0.0.0/8
    option                  redispatch
    retries                 3
    timeout http-request    10s
    timeout queue           1m
    timeout connect         10s
    timeout client          1m
    timeout server          1m
    timeout http-keep-alive 10s
    timeout check           10s
    maxconn                 3000
EOF

    print FILE <<EOF;

#---------------------------------------------------------------------
# main frontend which proxys to the backends
#---------------------------------------------------------------------
frontend  main
    bind *:5000
    acl url_static       path_beg       -i /static /images /javascript /stylesheets
    acl url_static       path_end       -i .jpg .gif .png .css .js

    use_backend static          if url_static
    default_backend             app

#---------------------------------------------------------------------
# static backend for serving up images, stylesheets and such
#---------------------------------------------------------------------
backend static
    balance     roundrobin
    server      static 127.0.0.1:4331 check

#---------------------------------------------------------------------
# round robin balancing between the various backends
#---------------------------------------------------------------------
backend app
    balance     roundrobin
    server  app1 127.0.0.1:5001 check
    server  app2 127.0.0.1:5002 check
    server  app3 127.0.0.1:5003 check
    server  app4 127.0.0.1:5004 check

EOF

    close(FILE);

    &General::system_background('/usr/local/bin/haproxyctrl', 'restart');
}

