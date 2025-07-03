# SmoothWall CGIs
#
# This code is distributed under the terms of the GPL
#
# (c) The SmoothWall Team
# Copyright (C) 2002 Alex Hudson - getcgihash() rewrite
# Copyright (C) 2002 Bob Grant <bob@cache.ucr.edu> - validmac()
# Copyright (c) 2002/04/13 Steve Bootes - add alias section, helper functions
# Copyright (c) 2002/08/23 Mark Wormgoor <mark@wormgoor.com> validfqdn()
# Copyright (c) 2003/09/11 Darren Critchley <darrenc@telus.net> srtarray()
#
package Header;

use CGI();
use File::Basename;
use HTML::Entities();
use Socket;
use Time::Local;
use Unicode::Normalize;

our %color = ();
&General::readhash("/srv/web/ipfire/html/themes/ipfire/include/colors.txt", \%color);

$|=1; # line buffering

$Header::revision = 'final';
$Header::swroot = '/var/ipfire';
$Header::graphdir='/srv/web/ipfire/html/graphs';
$Header::pagecolour = '#ffffff';
$Header::bordercolour = '#363636';
$Header::table1colour = '#f5f5f5';
$Header::table2colour = '#fafafa';
$Header::colourred = '#993333';
$Header::colourorange = '#FF9933';
$Header::colouryellow = '#FFFF00';
$Header::colourgreen = '#339933';
$Header::colourblue = '#333399';
$Header::colourovpn = '#339999';
$Header::colourwg = '#ff007f';
$Header::colourfw = '#000000';
$Header::colourvpn = '#990099';
$Header::colourerr = '#FF0000';
$Header::viewsize = 150;
$Header::errormessage = '';
$Header::extraHead = <<END
<style>
	.color20 {
		background-color: $color{'color20'};
	}
	.color22 {
		background-color: $color{'color22'};
	}
	.colouryellow {
		background-color: $Header::colouryellow;
	}
	.orange {
		background-color: orange;
	}	
	.red {
		background-color: red;
	}			
	.table1colour {
		background-color: $Header::table1colour;
	}
	.table2colour {
		background-color: $Header::table2colour;
	}
	.percent-box {
		border-style: solid;
		border-width: 1px;
		border-color: #a0a0a0;
		width: 100px;
		height: 10px;
	}
	.percent-bar {
		background-color: #a0a0a0;
		border-style: solid;
		border-width: 1px;
		border-color: #e2e2e2;
	}
	.percent-space {
		background-color: #e2e2e2;
		border-style: solid;
		border-width: 1px;
		border-color: #e2e2e2;
	}
</style>
END
;
my %menuhash = ();
my $menu = \%menuhash;
%settings = ();
%ethsettings = ();
%pppsettings = ();
my @URI = split('\?', $ENV{'REQUEST_URI'});

### Make sure this is an SSL request
if ($ENV{'SERVER_ADDR'} && $ENV{'HTTPS'} ne 'on') {
    print "Status: 302 Moved\r\n";
    print "Location: https://$ENV{'SERVER_ADDR'}:444/$ENV{'PATH_INFO'}\r\n\r\n";
    exit 0;
}

### Initialize environment
&General::readhash("${swroot}/main/settings", \%settings);
&General::readhash("${swroot}/ethernet/settings", \%ethsettings);
&General::readhash("${swroot}/ppp/settings", \%pppsettings);
$hostname = $settings{'HOSTNAME'};
$hostnameintitle = 0;

### Initialize language
require "${swroot}/lang.pl";
$language = &Lang::FindWebLanguage($settings{"LANGUAGE"});

### Read English Files
if ( -d "/var/ipfire/langs/en/" ) {
    opendir(DIR, "/var/ipfire/langs/en/");
    @names = readdir(DIR) or die "Cannot Read Directory: $!\n";
    foreach $name(@names) {
        next if ($name eq ".");
        next if ($name eq "..");
        next if (!($name =~ /\.pl$/));
        require "${swroot}/langs/en/${name}";
    };
};


### Enable Language Files
if ( -d "/var/ipfire/langs/${language}/" ) {
    opendir(DIR, "/var/ipfire/langs/${language}/");
    @names = readdir(DIR) or die "Cannot Read Directory: $!\n";
    foreach $name(@names) {
        next if ($name eq ".");
        next if ($name eq "..");
        next if (!($name =~ /\.pl$/));
        require "${swroot}/langs/${language}/${name}";
    };
};

### Initialize user manual
my %manualpages = ();
&_read_manualpage_hash("${General::swroot}/main/manualpages");

### Load selected language and theme functions
require "${swroot}/langs/en.pl";
require "${swroot}/langs/${language}.pl";
eval `/bin/cat /srv/web/ipfire/html/themes/ipfire/include/functions.pl`;

sub green_used() {
    if ($ethsettings{'GREEN_DEV'} && $ethsettings{'GREEN_DEV'} ne "") {
        return 1;
    }

    return 0;
}

sub orange_used () {
    if ($ethsettings{'CONFIG_TYPE'} =~ /^[24]$/) {
	return 1;
    }
    return 0;
}

sub blue_used () {
    if ($ethsettings{'CONFIG_TYPE'} =~ /^[34]$/) {
	return 1;
    }
    return 0;
}

sub is_modem {
    if ($ethsettings{'CONFIG_TYPE'} =~ /^[0]$/) {
	return 1;
    }
    return 0;
}

### Initialize menu
sub genmenu {

    my %subsystemhash = ();
    my $subsystem = \%subsystemhash;

    my %substatushash = ();
    my $substatus = \%substatushash;

    my %subnetworkhash = ();
    my $subnetwork = \%subnetworkhash;

    my %subserviceshash = ();
    my $subservices = \%subserviceshash;

    my %subfirewallhash = ();
    my $subfirewall = \%subfirewallhash;

    my %subipfirehash = ();
    my $subipfire = \%subipfirehash;

    my %sublogshash = ();
    my $sublogs = \%sublogshash;

  if ( -e "/var/ipfire/main/gpl_accepted") {

    eval `/bin/cat /var/ipfire/menu.d/*.menu`;
    eval `/bin/cat /var/ipfire/menu.d/*.main`;

    if (! blue_used()) {
	$menu->{'05.firewall'}{'subMenu'}->{'60.wireless'}{'enabled'} = 0;
    }
    if ( $ethsettings{'CONFIG_TYPE'} =~ /^(1|2|3|4)$/ && $ethsettings{'RED_TYPE'} eq 'STATIC' ) {
	$menu->{'03.network'}{'subMenu'}->{'70.aliases'}{'enabled'} = 1;
    }

    if (&General::RedIsWireless()) {
        $menu->{'01.system'}{'subMenu'}->{'21.wlan'}{'enabled'} = 1;
    }

    if ( $ethsettings{'RED_TYPE'} eq "PPPOE" && $pppsettings{'MONPORT'} ne "" ) {
        $menu->{'02.status'}{'subMenu'}->{'74.modem-status'}{'enabled'} = 1;
    }

	# Disable the Dialup/PPPoE menu item when the RED interface is in IP mode
	# (the "Network" module is loaded by general-functions.pl)
	if(&Network::is_red_mode_ip()) {
		$menu->{'01.system'}{'subMenu'}->{'20.dialup'}{'enabled'} = 0;
	}

    # Disbale unusable things in cloud environments
    if (&General::running_in_cloud()) {
        $menu->{'03.network'}{'subMenu'}->{'30.dhcp'}{'enabled'} = 0;
        $menu->{'03.network'}{'subMenu'}->{'80.macadressmenu'}{'enabled'} = 0;
        $menu->{'03.network'}{'subMenu'}->{'90.wakeonlan'}{'enabled'} = 0;
    }
  }
}

sub showhttpheaders
{
	print "Cache-control: private\n";
	print "Content-type: text/html; charset=UTF-8\n\n";
}

sub is_menu_visible($) {
    my $link = shift;
    $link =~ s#\?.*$##;
    return (-e $ENV{'DOCUMENT_ROOT'}."/../$link");
}


sub getlink($) {
    my $root = shift;
    if (! $root->{'enabled'}) {
	return '';
    }
    if ($root->{'uri'} !~ /^$/) {
	my $vars = '';
	if ($root->{'vars'} !~ /^$/) {
	    $vars = '?'. $root->{'vars'};
	}
	if (! is_menu_visible($root->{'uri'})) {
	    return '';
	}
	return $root->{'uri'}.$vars;
    }
    my $submenus = $root->{'subMenu'};
    if (! $submenus) {
	return '';
    }
    foreach my $item (sort keys %$submenus) {
	my $link = getlink($submenus->{$item});
	if ($link ne '') {
	    return $link;
	}
    }
    return '';
}


sub compare_url($) {
    my $conf = shift;

    my $uri = $conf->{'uri'};
    my $vars = $conf->{'vars'};
    my $novars = $conf->{'novars'};

    if ($uri eq '') {
	return 0;
    }
    if ($uri ne $URI[0]) {
	return 0;
    }
    if ($novars) {
	if ($URI[1] !~ /^$/) {
	    return 0;
	}
    }
    if (! $vars) {
	return 1;
    }
    return ($URI[1] eq $vars);
}


sub gettitle($) {
    my $root = shift;

    if (! $root) {
	return '';
    }
    foreach my $item (sort keys %$root) {
	my $val = $root->{$item};
	if (compare_url($val)) {
	    $val->{'selected'} = 1;
	    if ($val->{'title'} !~ /^$/) {
		return $val->{'title'};
	    }
	    return 'EMPTY TITLE';
	}

	my $title = gettitle($val->{'subMenu'});
	if ($title ne '') {
	    $val->{'selected'} = 1;
	    return $title;
	}
    }
    return '';
}

sub getcgihash {
	my ($hash, $params) = @_;
	my $cgi = CGI->new ();
	$hash->{'__CGI__'} = $cgi;
	return if ($ENV{'REQUEST_METHOD'} ne 'POST');
	if (!$params->{'wantfile'}) {
		$CGI::DISABLE_UPLOADS = 1;
		$CGI::POST_MAX        = 1024 * 1024;
	} else {
		$CGI::POST_MAX = 10 * 1024 * 1024;
	}

	$cgi->referer() =~ m/^https?\:\/\/([^\/]+)/;
	my $referer = $1;
	$cgi->url() =~ m/^https?\:\/\/([^\/]+)/;
	my $servername = $1;
	return if ($referer ne $servername);

	### Modified for getting multi-vars, split by |
	%temp = $cgi->Vars();
        foreach my $key (keys %temp) {
		$hash->{$key} = $temp{$key};
		$hash->{$key} =~ s/\0/|/g;
		$hash->{$key} =~ s/^\s*(.*?)\s*$/$1/;
        }

	if (($params->{'wantfile'})&&($params->{'filevar'})) {
		$hash->{$params->{'filevar'}} = $cgi->upload
						($params->{'filevar'});
	}
	return;
}

sub escape($) {
	my $s = shift;
	return HTML::Entities::encode_entities($s);
}

sub normalize($) {
	my $s = shift;

	# Remove any special characters
	$s = &Unicode::Normalize::NFKD($s);

	# Remove any whitespace and replace with dash
	$s =~ s/\s+/\-/g;

	return $s;
}

sub cleanhtml {
	my $outstring =$_[0];
	$outstring =~ tr/,/ / if not defined $_[1] or $_[1] ne 'y';

	return escape($outstring);
}

sub connectionstatus
{
    my %pppsettings = ();
    my %netsettings = ();
    my $iface='';

    $pppsettings{'PROFILENAME'} = 'None';
    &General::readhash("${General::swroot}/ppp/settings", \%pppsettings);
    &General::readhash("${General::swroot}/ethernet/settings", \%netsettings);

    my $profileused='';
    unless ( $netsettings{'RED_TYPE'} =~ /^(DHCP|STATIC)$/ ) {
    	$profileused="- $pppsettings{'PROFILENAME'}";
    }

    my ($timestr, $connstate);

		my $connstate = "<span>$Lang::tr{'idle'} $profileused</span>";

		if (-e "${General::swroot}/red/active") {
			$timestr = &General::age("${General::swroot}/red/active");
			$connstate = "<span>$Lang::tr{'connected'} - (<span>$timestr</span>) $profileused</span>";
		} else {
		  if ((open(KEEPCONNECTED, "</var/ipfire/red/keepconnected") == false) && ($pppsettings{'RECONNECTION'} eq "persistent")) {
				$connstate = "<span>$Lang::tr{'connection closed'} $profileused</span>";
      } elsif (($pppsettings{'RECONNECTION'} eq "dialondemand") && ( -e "${General::swroot}/red/dial-on-demand")) {
				$connstate = "<span>$Lang::tr{'dod waiting'} $profileused</span>";
			} else {
				$connstate = "<span>$Lang::tr{'connecting'} $profileused</span>" if (system("ps -ef | grep -q '[p]ppd'"));
			}
		}
		
    return $connstate;
}

sub CheckSortOrder {
#Sorting of allocated leases
    if ($ENV{'QUERY_STRING'} =~ /^IPADDR|^ETHER|^HOSTNAME|^ENDTIME/ ) {
        my $newsort=$ENV{'QUERY_STRING'};
        &General::readhash("${swroot}/dhcp/settings", \%dhcpsettings);
        $act=$dhcpsettings{'SORT_LEASELIST'};
        #Reverse actual ?
        if ($act =~ $newsort) {
            if ($act !~ 'Rev') {$Rev='Rev'};
            $newsort.=$Rev
        };

        $dhcpsettings{'SORT_LEASELIST'}=$newsort;
        &General::writehash("${swroot}/dhcp/settings", \%dhcpsettings);
        $dhcpsettings{'ACTION'} = 'SORT';  # avoid the next test "First lauch"
    }

}

sub PrintActualLeases
{
    &openbox('100%', 'left', $Lang::tr{'current dynamic leases'});
    print <<END
<table width='100%' class='tbl'>
<tr>
<th width='25%' align='center'><a href='$ENV{'SCRIPT_NAME'}?IPADDR'><b>$Lang::tr{'ip address'}</b></a></th>
<th width='25%' align='center'><a href='$ENV{'SCRIPT_NAME'}?ETHER'><b>$Lang::tr{'mac address'}</b></a></th>
<th width='20%' align='center'><a href='$ENV{'SCRIPT_NAME'}?HOSTNAME'><b>$Lang::tr{'hostname'}</b></a></th>
<th width='25%' align='center'><a href='$ENV{'SCRIPT_NAME'}?ENDTIME'><b>$Lang::tr{'lease expires'} (local time d/m/y)</b></a></th>
<th width='5%' align='center'><b>$Lang::tr{'dhcp make fixed lease'}</b></th>
</tr>
END
;

    open(LEASES,"/var/state/dhcp/dhcpd.leases") or die "Can't open dhcpd.leases";
	while (my $line = <LEASES>) {
		next if( $line =~ /^\s*#/ );
		chomp($line);
		@temp = split (' ', $line);

		if ($line =~ /^\s*lease/) {
			$ip = $temp[1];
			#All field are not necessarily read. Clear everything
			$endtime = 0;
			$endtime_print = "";
			$expired = 0;
			$ether = "";
			$hostname = "";
		}

		if ($line =~ /^\s*ends/) {
			$line =~ /(\d+)\/(\d+)\/(\d+) (\d+):(\d+):(\d+)/;
			$endtime = timegm($6, $5, $4, $3, $2 - 1, $1 - 1900);
			($sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $dst) = localtime($endtime);
			$endtime_print = sprintf ("%02d/%02d/%d %02d:%02d:%02d",$mday,$mon+1,$year+1900,$hour,$min,$sec);
			$expired = $endtime < time();
		}

		if ($line =~ /^\s*hardware ethernet/) {
			$ether = $temp[2];
			$ether =~ s/;//g;
		}

		if ($line =~ /^\s*client-hostname/) {
			$hostname = "$temp[1] $temp[2] $temp[3]";
			$hostname =~ s/\"|[;\s]+?$//g; # remove quotes, trim semicolon and white space
		}

		if ($line eq "}") {
			@record = ('IPADDR',$ip,'ENDTIME',$endtime,'ETHER',$ether,'HOSTNAME',$hostname,'endtime_print',$endtime_print,'expired',$expired);
			$record = {};								# create a reference to empty hash
			%{$record} = @record;						# populate that hash with @record
			$entries{$record->{'IPADDR'}} = $record;	# add this to a hash of hashes
		}
    }
    close(LEASES);

    my $id = 0;
    my $col = "";
	my $divider_printed = 0;
    foreach my $key (sort leasesort keys %entries) {
		my $hostname = &cleanhtml($entries{$key}->{HOSTNAME},"y");
		my $hostname_print = $hostname;
		if($hostname_print eq "") { #print blank space if no hostname is found
			$hostname_print = "&nbsp;&nbsp;&nbsp;";
		}
		
		# separate active and expired leases with a horizontal line
		if(($entries{$key}->{expired}) && ($divider_printed == 0)) {
			$divider_printed = 1;
			if ($id % 2) {
				print "<tr><td colspan='5' bgcolor='$table1colour'><hr size='1'></td></tr>\n";
			} else {
				print "<tr><td colspan='5' bgcolor='$table2colour'><hr size='1'></td></tr>\n";
			}
			$id++;
		}
		
		print "<form method='post' action='/cgi-bin/dhcp.cgi'><tr>\n";
		if ($id % 2) {
			$col="bgcolor='$table1colour'";
		} else {
			$col="bgcolor='$table2colour'";
		}
		
		if($entries{$key}->{expired}) {
			print <<END
<td align='center' $col><input type='hidden' name='FIX_ADDR' value='$entries{$key}->{IPADDR}' /><strike><i>$entries{$key}->{IPADDR}</i></strike></td>
<td align='center' $col><input type='hidden' name='FIX_MAC' value='$entries{$key}->{ETHER}' /><strike><i>$entries{$key}->{ETHER}</i></strike></td>
<td align='center' $col><input type='hidden' name='FIX_REMARK' value='$hostname' /><strike><i>$hostname_print<i><strike></td>
<td align='center' $col><input type='hidden' name='FIX_ENABLED' value='on' /><strike><i>$entries{$key}->{endtime_print}</i></strike></td>
END
;
		} else {
			print <<END
<td align='center' $col><input type='hidden' name='FIX_ADDR' value='$entries{$key}->{IPADDR}' />$entries{$key}->{IPADDR}</td>
<td align='center' $col><input type='hidden' name='FIX_MAC' value='$entries{$key}->{ETHER}' />$entries{$key}->{ETHER}</td>
<td align='center' $col><input type='hidden' name='FIX_REMARK' value='$hostname' />$hostname_print</td>
<td align='center' $col><input type='hidden' name='FIX_ENABLED' value='on' />$entries{$key}->{endtime_print}</td>
END
;
		}

		print <<END
<td $col><input type='hidden' name='ACTION' value='$Lang::tr{'add'}2' /><input type='submit' name='SUBMIT' value='$Lang::tr{'add'}' /></td>
</tr></form>
END
;
		$id++;
    }

    print "</table>";
    &closebox();
}


# This sub is used during display of actives leases
sub leasesort {
	if (rindex ($dhcpsettings{'SORT_LEASELIST'},'Rev') != -1)
	{
		$qs=substr ($dhcpsettings{'SORT_LEASELIST'},0,length($dhcpsettings{'SORT_LEASELIST'})-3);
		if ($qs eq 'IPADDR') {
			@a = split(/\./,$entries{$a}->{$qs});
			@b = split(/\./,$entries{$b}->{$qs});
			$entries{$a}->{'expired'} <=> $entries{$b}->{'expired'} || # always sort by expiration first
			($b[0]<=>$a[0]) ||
			($b[1]<=>$a[1]) ||
			($b[2]<=>$a[2]) ||
			($b[3]<=>$a[3]);
		} else {
			$entries{$a}->{'expired'} <=> $entries{$b}->{'expired'} ||
			$entries{$b}->{$qs} cmp $entries{$a}->{$qs};
		}
	}
	else #not reverse
	{
		$qs=$dhcpsettings{'SORT_LEASELIST'};
		if ($qs eq 'IPADDR') {
			@a = split(/\./,$entries{$a}->{$qs});
			@b = split(/\./,$entries{$b}->{$qs});
			$entries{$a}->{'expired'} <=> $entries{$b}->{'expired'} ||
			($a[0]<=>$b[0]) ||
			($a[1]<=>$b[1]) ||
			($a[2]<=>$b[2]) ||
			($a[3]<=>$b[3]);
		} else {
			$entries{$a}->{'expired'} <=> $entries{$b}->{'expired'} ||
			$entries{$a}->{$qs} cmp $entries{$b}->{$qs};
		}
	}
}

sub colorize {
	my $string =  $_[0];
	my @array = split(/\//,$string);
	my $string2 = $array[0];

	if ( $string eq "*" or $string eq "" ){
		return $string;
	} elsif ( $string =~ "ipsec" ){
		return "<font color='".${Header::colourvpn}."'>".$string."</font>";
	} elsif ( $string =~ "tun" ){
		return "<font color='".${Header::colourovpn}."'>".$string."</font>";
	} elsif ( $string =~ "lo" or $string =~ "127.0.0.0" ){
		return "<font color='".${Header::colourfw}."'>".$string."</font>";
	} elsif ( $string =~ $ethsettings{'GREEN_DEV'} or &General::IpInSubnet($string2,$ethsettings{'GREEN_NETADDRESS'},$ethsettings{'GREEN_NETMASK'}) ){
		return "<font color='".${Header::colourgreen}."'>".$string."</font>";
	} elsif (  $string =~ "ppp0" or $string =~ $ethsettings{'RED_DEV'} or $string =~ "0.0.0.0" or $string =~ $ethsettings{'RED_ADDRESS'} ){
		return "<font color='".${Header::colourred}."'>".$string."</font>";
	} elsif ( $ethsettings{'CONFIG_TYPE'}>1 and ( $string =~ $ethsettings{'BLUE_DEV'} or &General::IpInSubnet($string2,$ethsettings{'BLUE_NETADDRESS'},$ethsettings{'BLUE_NETMASK'}) )){
		return "<font color='".${Header::colourblue}."'>".$string."</font>";
	} elsif ( $ethsettings{'CONFIG_TYPE'}>2 and ( $string =~ $ethsettings{'ORANGE_DEV'} or &General::IpInSubnet($string2,$ethsettings{'ORANGE_NETADDRESS'},$ethsettings{'ORANGE_NETMASK'}) )){
		return "<font color='".${Header::colourorange}."'>".$string."</font>";
	} else {
		return $string;
	}
}

# Get user manual URL for a configuration page inside the "/cgi-bin/"
# (reads current page from the environment variables unless defined)
# Returns empty if no URL is available
sub get_manualpage_url() {
	my ($cgifile) = @_;
	$cgifile //= substr($ENV{'SCRIPT_NAME'}, 9); # remove fixed "/cgi-bin/" path

	# Ensure base url is configured
	return unless($manualpages{'BASE_URL'});

	# Return URL
	if($cgifile && defined($manualpages{$cgifile})) {
		return "$manualpages{'BASE_URL'}/$manualpages{$cgifile}";
	}

	# No manual page configured, return nothing
	return;
}

# Private function to load a hash of configured user manual pages from file
# (run check_manualpages.pl to make sure the file is correct)
sub _read_manualpage_hash() {
	my ($filename) = @_;

	open(my $file, "<", $filename) or return; # Fail silent
	while(my $line = <$file>) {
		chomp($line);
		next if(substr($line, 0, 1) eq '#'); # Skip comments
		next if(index($line, '=', 1) == -1); # Skip incomplete lines

		my($left, $value) = split(/=/, $line, 2);
		if($left =~ /^([[:alnum:]\/._-]+)$/) {
			my $key = $1;
			$manualpages{$key} = $value;
		}
	}
	close($file);
}

1; # End of package "Header"
