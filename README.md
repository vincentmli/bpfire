# BPFire - eBPF Network Firewall and Load Balancer  (eBPF 网络防火墙及负载均衡）

# What is BPFire?

BPFire is fork of [IPFire 2.x](https://github.com/ipfire/ipfire-2.x), a hardened, versatile, state-of-the-art Open Source firewall based on Linux. BPFire is to enable revolutionary [eBPF](https://ebpf.io/) technology for non-tech savvy users, make eBPF technology consumable to home users or any size of organizations to secure their network environment. Current supported eBPF network application features:

BPFire 基于IPFire 2.x, 一个基于Linux的安全坚固、多功能、先进的开源防火墙. BPFire 为普罗大众带来革命创新性的eBPF技术，为家庭用户或任何大小组织企业的网络安全保驾护航. 当前支持的eBPF应用包括：

1. XDP DDoS protection, See XDP SYNPROXY stops 10G DDoS SYN flood [here](https://www.youtube.com/watch?v=81Hgoy-x1A4)
2. XDP DNS domain blocklist, ratelimit protection
3. XDP SSL/TLS server name indicator (SNI) blocklist
4. XDP GeoIP/Country blocklist
5. XDP multi attachment and capture mode for Intrusion Detection System Suricata in IPS mode
6. eBPF based LoxiLB load balancer, Firewall, Proxy, see full features [LoxiLB](https://loxilb-io.github.io/loxilbdocs/#overall-features-of-loxilb)

# Where can I get BPFire installation ISO or flash image?

http://bpfire.net/download/

https://drive.google.com/drive/folders/1HPJTWP6wi5gPd5gyiiKvIhWipqguptzZ?usp=drive_link

# What computer hardwares BPFire requires?

BPFire support commodity computer hardware, small or large, old or new, cheap or expensive.

for example [mini PC](https://www.aliexpress.com/w/wholesale-home-firewall-router.html?spm=a2g0o.best.search.0) I use at home.

# How do I install BPFire?

flash the ISO to USB on Linux machine, /dev/sdc is your USB thrumb drive.

dd if=bpfire-2.29-core184-x86_64.iso of=/dev/sdc status=progress

BPFire installation on mini industrial PC:

[![BPFire installation on mini industrial PC](http://img.youtube.com/vi/p9iHCe0hXPs/0.jpg)](https://www.youtube.com/watch?v=p9iHCe0hXPs "BPFire installation on mini industrial PC")

# How do I use this software?

BPFire XDP DDoS feature demo:

[![Enable IPFire eBPF XDP DDoS from WebUI](http://img.youtube.com/vi/1pdNgoP-Kho/0.jpg)](https://www.youtube.com/watch?v=1pdNgoP-Kho "Enable IPFire eBPF XDP DDoS from WebUI")

IPFire have a long and detailed wiki located [here](https://wiki.ipfire.org/) which
should answers most of your questions for IPFire.

# BPFire SYNPROXY throughput with and without XDP acceleration under 10Gbit DDoS SYN flood:

[![Throughput performance](http://img.youtube.com/vi/81Hgoy-x1A4/0.jpg)](https://www.youtube.com/watch?v=81Hgoy-x1A4 "Throughput performance")


# BPFire WebUI screenshot:

English:

![](./images/bpfire-lb-en.png)

![](./images/en-1.png)

![](./images/en-2.png)

Chinese:

![](./images/bpfire-lb-zh.png)

![](./images/cn-1.png)

![](./images/cn-2.png)

# Does BPFire run in hypervisor virtual environment?

Yes, We have tested in Linux KVM hypervisor, Proxmox, Microsoft Hyper-v, should support Virtualbox, VMware as well.

Microsoft Hyper-v screen shot:

![](./images/hyperv-1.png)

![](./images/hyperv-2.png)

# But I have some questions left. Where can I get support?

You can ask your question by open github issue report or discussion or
You can ask your question at ipfire community located [here](https://community.ipfire.org/) that is IPFire related.

# How to build BPFire?

Build Environment Setup https://www.ipfire.org/docs/devel/ipfire-2-x/build-initial

git clone https://github.com/vincentmli/BPFire.git

cd BPFire

git checkout bpfire

get BPFire source tar ball cache.tar https://drive.google.com/drive/folders/15rEoiB9TU4DxYv1qdOFqyJ2DkL6J9lG1?usp=drive_link

tar xvf cache.tar

get all BPFire addon source tar balls from https://drive.google.com/drive/folders/1cDZ0z26td2jVkxBX9cHhz43QxrZn3Aqq?usp=drive_link and move them to cache directory

mv *.tar.gz ./cache/

./make.sh clean

./make.sh build

# How do I support BPFire development?

Join or [Donate to BPFire paypal](https://www.paypal.com/donate/?business=BL97G8687E5B6&no_recurring=0&item_name=Make+revolutionary+eBPF+technology+available+for+non-tech+savvy+users+for+safe+online+surfing&currency_code=USD)
