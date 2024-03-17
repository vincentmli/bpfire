#!/usr/bin/perl
###############################################################################
#                                                                             #
# IPFire.org - A linux based firewall                                         #
# Copyright (C) 2007-2020  IPFire Team  <info@ipfire.org>                     #
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
my %cgiparams=();
my %checked=();
my $errormessage='';
my $counter = 0;
my %tcp_ports=();
my $portfile = "${General::swroot}/ddos/tcp_ports";
my $ddossettingfile = "${General::swroot}/ddos/settings";

&get_tcp_ports();

# Read configuration file.
&General::readhash("$ddossettingfile", \%ddossettings);

&General::readhash("${General::swroot}/main/settings", \%mainsettings);
&General::readhash("/srv/web/ipfire/html/themes/ipfire/include/colors.txt", \%color);

&Header::showhttpheaders();

$ddossettings{'ENABLE_DDOS'} = 'off';
$ddossettings{'ACTION'} = '';
&Header::getcgihash(\%cgiparams);

if ($cgiparams{'ACTION'} eq $Lang::tr{'save'})
{

	if (exists $cgiparams{'ENABLE_DDOS'}) {
		$ddossettings{'ENABLE_DDOS'} = "on";
		&General::log($Lang::tr{'ddos is enabled'});
		&General::system('/usr/bin/touch', "${General::swroot}/ddos/enableddos");
		#system('/usr/local/bin/sshctrl') == 0
		#	or $errormessage = "$Lang::tr{'bad return code'} " . $?/256;
	} else {
		$ddossettings{'ENABLE_DDOS'} = "off";
		&General::log($Lang::tr{'ddos is disabled'});
		unlink "${General::swroot}/ddos/enableddos";
	}

        # Loop through our locations array to prevent from
        # non existing countries or code.
        foreach my $p (values %tcp_ports) {
                # Check if blocking for this country should be enabled/disabled.
                if (exists $cgiparams{$p}) {
                        $ddossettings{$p} = "on";
                } else {
                        $ddossettings{$p} = "off";
                }
        }
	&General::writehash("$ddossettingfile", \%ddossettings);

}

# Read configuration file.
&General::readhash("$ddossettingfile", \%ddossettings);

&Header::openpage($Lang::tr{'ebpf xdp ddos'}, 1, '');

# Checkbox pre-selection.
my $checked;
if ($ddossettings{'ENABLE_DDOS'} eq "on") {
        $checked = "checked='checked'";
}

&Header::openbigbox('100%', 'left', '', $errormessage);

if ($errormessage) {
	&Header::openbox('100%', 'left', $Lang::tr{'error messages'});
	print "<font class='base'>$errormessage&nbsp;</font>\n";
	&Header::closebox();
}

# Print box to enable/disable locationblock.
print"<form method='POST' action='$ENV{'SCRIPT_NAME'}'>\n";

&Header::openbox('100%', 'center', $Lang::tr{'xdp'});
print <<END;
        <table width='95%'>
                <tr>
                        <td width='50%' class='base'>$Lang::tr{'xdp enable'}
                        <td><input type='checkbox' name='ENABLE_DDOS' $checked></td>
                        <td align='center'><input type='submit' name='ACTION' value='$Lang::tr{'save'}'></td>
                </tr>
        </table>

END

&Header::closebox();

&Header::openbox('100%', 'center', $Lang::tr{'xdp port'});
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

&Header::openbox('100%', 'center', $Lang::tr{'xdp status'});

print <<END;
		<table class="tbl" width="100%">
			<thead>
				<tr>
					<th align="center">
						<strong>$Lang::tr{'xdp interface'}</strong>
					</th>
					<th align="center">
						<strong>$Lang::tr{'xdp prio'}</strong>
					</th>
					<th align="center">
						<strong>$Lang::tr{'xdp program'}</strong>
					</th>
					<th align="center">
						<strong>$Lang::tr{'xdp mode'}</strong>
					</th>
					<th align="center">
						<strong>$Lang::tr{'xdp id'}</strong>
					</th>
					<th align="center">
						<strong>$Lang::tr{'xdp tag'}</strong>
					</th>
					<th align="center">
						<strong>$Lang::tr{'xdp action'}</strong>
					</th>
				</tr>
			</thead>
			<tbody>
END

&printxdp();

print "</tbody>\n</table>\n";

&Header::closebox();

&Header::closebigbox();

&Header::closepage();

sub get_tcp_ports()
{
	open(my $fh, '<', $portfile) or die "Unable to open file: $!";
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
	my @output = &General::system_output("xdp-loader", "status");
	chomp(@output);

		# list active logins...
		foreach my $line (@output)
		{
			#next if $line  !~ /^red0/;
			#next if $line  !~ /^\s=>/;
			my @arry = split(/\ +/, $line);

			my $interface = $arry[0];
			my $prio = $arry[1];
			my $prog = $arry[2];
			my $mode = $arry[3];
			my $id = $arry[4];
			my $tag = $arry[5];
			my $action = $arry[6];

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
