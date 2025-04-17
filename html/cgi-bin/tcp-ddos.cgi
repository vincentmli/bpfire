#!/usr/bin/perl
###############################################################################
#                                                                             #
# Copyright (C) 2024-2025  BPFire <vincent.mc.li@gmail.com>                     #
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
#use CGI::Carp 'fatalsToBrowser';

use IO::Socket;

require '/var/ipfire/general-functions.pl';
require "${General::swroot}/location-functions.pl";
require "${General::swroot}/lang.pl";
require "${General::swroot}/header.pl";

my %color = ();
my %mainsettings = ();
my %ddossettings=();
my %checked=();
my $errormessage='';
my $counter = 0;
my %tcp_ports=();
my %udp_ports=();
my $tcp_portfile = "${General::swroot}/ddos/tcp_ports";
my $ddossettingfile = "${General::swroot}/ddos/tcp-ddos-settings";

&get_tcp_ports();

# Read configuration file.

&General::readhash("${General::swroot}/main/settings", \%mainsettings);
&General::readhash("/srv/web/ipfire/html/themes/ipfire/include/colors.txt", \%color);

&Header::showhttpheaders();

$ddossettings{'ENABLE_TCP_DDOS'} = 'off';
$ddossettings{'ACTION'} = '';

&Header::getcgihash(\%ddossettings);

if ($ddossettings{'ACTION'} eq $Lang::tr{'save'})
{

        # Loop through our locations array to prevent from
        # non existing countries or code.
        foreach my $p (values %tcp_ports) {
                # Check if blocking for this country should be enabled/disabled.
                if (exists $ddossettings{$p}) {
                        $ddossettings{$p} = "on";
                } else {
                        $ddossettings{$p} = "off";
                }
        }

	&General::writehash("$ddossettingfile", \%ddossettings);

	if ($ddossettings{'ENABLE_TCP_DDOS'} eq 'on') {
		&General::system('/usr/bin/touch', "${General::swroot}/ddos/enabletcpddos");
		&General::system('/usr/local/bin/tcpddosctrl', 'start');
	} else {
		&General::system('/usr/local/bin/tcpddosctrl', 'stop');
		unlink "${General::swroot}/ddos/enabletcpddos";
	}

}

&Header::openpage($Lang::tr{'xdp tcp ddos config'}, 1, '');

&Header::openbigbox('100%', 'left', '', $errormessage);

if ($errormessage) {
	&Header::openbox('100%', 'left', $Lang::tr{'error messages'});
	print "<font class='base' color=red>$errormessage&nbsp;</font>\n";
	&Header::closebox();
}

# Read configuration file.
&General::readhash("$ddossettingfile", \%ddossettings);

# Checkbox pre-selection.
my $checked;
if ($ddossettings{'ENABLE_TCP_DDOS'} eq "on") {
        $checked = "checked='checked'";
}

# Print box to enable/disable locationblock.
print"<form method='POST' action='$ENV{'SCRIPT_NAME'}'>\n";

&Header::openbox('100%', 'center', $Lang::tr{'xdp tcp ddos'});
print <<END;
        <table width='95%'>
                <tr>
                        <td width='50%' class='base'>$Lang::tr{'xdp tcp ddos enable'}
                        <td><input type='checkbox' name='ENABLE_TCP_DDOS' $checked></td>
                        <td align='center'><input type='submit' name='ACTION' value='$Lang::tr{'save'}'></td>
                </tr>
        </table>

END

&Header::closebox();

&Header::openbox('100%', 'center', $Lang::tr{'xdp tcp port'});
print <<END;

<table width='95%' class='tbl' id="countries">
        <tr>
                <td width='5%' align='center' bgcolor='$color{'color20'}'></td>
                <td width='5%' align='center' bgcolor='$color{'color20'}'>
                        <b>$Lang::tr{'port'}</b>
                </td>
                <td with='35%' align='left' bgcolor='$color{'color20'}'>
                        <b>$Lang::tr{'service'}</b>
                </td>

		<td width='5%' bgcolor='$color{'color20'}'>&nbsp;</td>

                <td width='5%' align='center' bgcolor='$color{'color20'}'></td>
                <td width='5%' align='center' bgcolor='$color{'color20'}'>
                        <b>$Lang::tr{'port'}</b>
                </td>
                <td with='35%' align='left' bgcolor='$color{'color20'}'>
                        <b>$Lang::tr{'service'}</b>
                </td>

        </tr>
END

my $lines;
my $lines2;
my $col;


# Sort output based on hash value port number
for my $service ( sort { $tcp_ports{$a} cmp $tcp_ports{$b} }
    keys %tcp_ports )
{
	my $port = $tcp_ports{$service};

        # Checkbox pre-selection.
        my $checked;
        if ($ddossettings{$port} eq "on") {
                $checked = "checked='checked'";
        }

        # Colour lines.
        if ($lines % 2) {
                $col="bgcolor='$color{'color20'}'";
        } else {
                $col="bgcolor='$color{'color22'}'";
        }

        # Grouping elements.
        my $line_start;
        my $line_end;
        if ($lines2 % 2) {
                # Increase lines (background color by once.
                $lines++;

                # Add empty column in front.
                $line_start="<td $col>&nbsp;</td>";

                # When the line number can be diveded by "2",
                # we are going to close the line.
                $line_end="</tr>";
        } else {
                # When the line number is  not divideable by "2",
                # we are starting a new line.
                $line_start="<tr>";
                $line_end;
        }

        print "$line_start<td align='center' $col><input type='checkbox' name='$port' $checked></td>\n";
	print "<td align='center' $col>$port</td>\n";
        print "<td align='left' $col>$service</td>$line_end\n";

$lines2++;
}

print <<END;
</table>

END

&Header::closebox();

print "</form>\n";

&Header::closebigbox();

&Header::closepage();

sub get_tcp_ports()
{
	my $fh;
	open($fh, '<', $tcp_portfile) or die "Unable to open file: $!";
	while (my $line = <$fh>) {
		chomp $line;
		next if $line =~ /^\s*#/; # Skip comments
		my ($service, $port) = $line =~ /^(\w+)\s+(\d+)\/tcp/;
		if ($service && $port) {
			$tcp_ports{$service} = $port;
		}
	}
	close($fh);
}

sub printxdp()
{
	# print active SSH logins (grep outpout of "who -s")
	my @output = &General::system_output("/usr/local/bin/tcpddosctrl", "status");
	chomp(@output);

		# list active logins...
		foreach my $line (@output)
		{
			my $interface;
			my $prio;
			my $prog;
			my $mode;
			my $id;
			my $tag;
			my $action;
			#comment next below when having issue
			#next if $line  !~ /^red0/;
			#next if $line  !~ /^\s=>/;
			next if $line =~ /No XDP program loaded!/;
			if ($line =~ /^red0/) {
				my @arry = split(/\s+/, $line);
				$interface = $arry[0];
				$prio = "N/A";
				$prog = $arry[1];
				$mode = $arry[2];
				$id = $arry[3];
				$tag = $arry[4];
				$action = "N/A";
			} elsif ($line =~ /^\s=>/) {
				my @arry = split(/\s+/, $line);
				$interface = "red0";
				$prio = $arry[2];
				$prog = $arry[3];
				$mode = "N/A";
				$id = $arry[4];
				$tag = $arry[5];
				$action = $arry[6];
			}
			if ($line =~ /^red0/ or $line =~ /^\s=>/) {
				my $table_colour = ($id % 2) ? $color{'color20'} : $color{'color22'};

				print <<END;
					<tr bgcolor='$table_colour'>
						<td>$interface</td>
						<td>$prio</td>
						<td>$prog</td>
						<td>$mode</td>
						<td>$id</td>
						<td>$tag</td>
						<td>$action</td>
					</tr>
END
;
			}

		}
}
