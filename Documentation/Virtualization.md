# Virtualization

You can also use (parts of) ICOc with various virtualization software. For that to work you have to make sure that (at least) the PEAK CAN adapter is attached to the virtual guest operating system. For some virtualization software you might have to install additional software for that to work. For example, [VirtualBox][] requires that you install the VirtualBox Extension Pack before you can use USB 2 and USB 3 devices.

> **Note:** Please be advised that the [**VirtualBox Extension Pack is paid software**](https://www.virtualbox.org/wiki/Licensing_FAQ) even though you can download and use it without any license key. **[Oracle might come after you, if you do not pay for the license](https://www.reddit.com/r/sysadmin/comments/d1ttzp/oracle_is_going_after_companies_using_virtualbox/)**, even if you use the Extension Pack in an educational setting.

The table below shows some of the virtualization software we tried and that worked (when we tested it).

| Virtualization Software    | Host OS | Host Architecture | Guest OS     | Guest Architecture | Notes                                                                                                                                            |
| -------------------------- | ------- | ----------------- | ------------ | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| [Parallels Desktop][]      | macOS   | `x64`             | Ubuntu 20.04 | `x64`              |                                                                                                                                                  |
| [Parallels Desktop][]      | macOS   | `x64`             | Windows 10   | `x64`              |                                                                                                                                                  |
| [Parallels Desktop][]      | macOS   | `ARM64`           | Fedora 36    | `ARM64`            |                                                                                                                                                  |
| [Parallels Desktop][]      | macOS   | `ARM64`           | Windows 11   | `ARM64`, `x64`     | JLink (and hence Simplicity Commander) only works with [programming adapters that support WinUSB](https://wiki.segger.com/J-Link_on_Windows_ARM) |
| [VirtualBox][]             | macOS   | `x64`             | Windows 10   | `x64`              |                                                                                                                                                  |
| [VirtualBox][]             | Windows | `x64`             | Fedora 36    | `x64`              |                                                                                                                                                  |
| [WSL 2](http://aka.ms/wsl) | Windows | `x64`             | Ubuntu 22.04 | `x64`              |                                                                                                                                                  |

[virtualbox]: https://www.virtualbox.org
[parallels desktop]: https://www.parallels.com

## Windows Subsystem for Linux 2

Using ICOc in the WSL 2 currently [requires using a custom Linux kernel](https://github.com/microsoft/WSL/issues/5533). We **would not recommend** using ICOc with this type of virtualization software, since the setup requires quite some amount of work and time. Nevertheless the steps below should show you how you can use the PEAK CAN adapter and hence ICOc with WSL 2.

1. Install WSL 2 (Windows Shell):

   ```
   wsl --install
   ```

2. Install Ubuntu 22.04 VM (Windows Shell):

   1. Install [Ubuntu 22.04 from the Microsoft Store](https://apps.microsoft.com/store/detail/ubuntu-2204-lts/9PN20MSR04DW)

   2. Open the Ubuntu 22.04 application

      1. Choose a user name
      2. Choose a password

   3. Execute the following commands in a Powershell session

      ```pwsh
      wsl --setdefault Ubuntu-22.04
      wsl --set-version Ubuntu-22.04 2
      ```

      The second command might fail, if `Ubuntu-22.04` already uses WSL 2. In this case please just ignore the error message.

3. [Create Custom Kernel](https://github.com/dorssel/usbipd-win/wiki/WSL-support#building-your-own-usbip-enabled-wsl-2-kernel)

   Windows Shell:

   > **Note:** Please replace `<user>` with your (Linux) username (e.g. `rene`)

   ```pwsh
   cd ~/Documents
   mkdir WSL
   cd WSL
   wsl --export Ubuntu-22.04 CANbuntu.tar
   wsl --import CANbuntu CANbuntu CANbuntu.tar
   wsl --distribution CANbuntu --user <user>
   ```

   Linux Shell:

   ```sh
   sudo apt update
   sudo apt upgrade -y
   sudo apt install -y bc build-essential flex bison libssl-dev libelf-dev \
                       libncurses-dev autoconf libudev-dev libtool dwarves
   cd ~
   git clone https://github.com/microsoft/WSL2-Linux-Kernel.git
   cd WSL2-Linux-Kernel
   uname -r # 5.15.74.2-microsoft-standard-WSL2 → branch …5.15.y
   git checkout linux-msft-wsl-5.15.y
   cat /proc/config.gz | gunzip > .config
   make menuconfig
   ```

   Make sure the following features are enabled:

   - `Device Drivers` → `USB Support`
   - `Device Drivers` → `USB Support` → `USB announce new devices`
   - `Device Drivers` → `USB Support` → `USB Modem (CDC ACM) support`
   - `Device Drivers` → `USB Support` → `USB/IP`
   - `Device Drivers` → `USB Support` → `USB/IP` → `VHCI HCD`
   - `Device Drivers` → `USB Support` → `USB Serial Converter Support`
   - `Device Drivers` → `USB Support` → `USB Serial Converter Support` → `USB FTDI Single port Serial Driver`

   Enable the following features:

   - `Networking support` → `CAN bus subsystem support`
   - `Networking support` → `CAN bus subsystem support` → `Raw CAN Protocol`
   - `Networking support` → `CAN bus subsystem support` → `CAN device drivers` → `Virtual Local CAN Interface`
   - `Networking support` → `CAN bus subsystem support` → `CAN device drivers` → `Serial / USB serial CAN Adaptors (slcan)`
   - `Networking support` → `CAN bus subsystem support` → `CAN device drivers` → → `CAN USB Interfaces` → `PEAK PCAN-USB/USB Pro interfaces for CAN 2.0b/CAN-FD`

   Save the modified kernel configuration.

   Linux Shell:

   ```sh
   touch .scmversion
   make
   sudo make modules_install
   sudo make install
   ```

4. Install `usbipd-win` (Linux Shell):

   ```sh
   cd tools/usb/usbip
   ./autogen.sh
   ./configure
   sudo make install
   sudo cp libsrc/.libs/libusbip.so.0 /lib/libusbip.so.0
   sudo apt-get install -y hwdata
   ```

5. Copy image (Linux Shell):

   > **Note:** Please replace `<user>` with your (Windows) username (e.g. `rene`)

   ```sh
   cd ~/WSL2-Linux-Kernel
   cp arch/x86/boot/bzImage /mnt/c/Users/<user>/Documents/WSL/canbuntu-bzImage
   ```

6. Create `.wslconfig` in (root of) Windows user directory and store the following text:

   ```ini
   [wsl2]
   kernel=c:\\users\\<user>\\Documents\\WSL\\canbuntu-bzImage
   ```

   > **Note:** Please replace `<user>` with your (Windows) username (e.g. `rene`)

7. Set default distribution (Windows Shell)

   ```sh
   wsl --setdefault CANbuntu
   ```

8. Shutdown and restart WSL (Windows Shell):

   ```pwsh
   wsl --shutdown
   wsl -d CANbuntu --cd "~"
   ```

9. Change default user of WSL distro (Linux Shell)

   ```
   sudo nano /etc/wsl.conf
   ```

   Insert the following text:

   ```ini
   [user]
   default=<user>
   ```

   > **Note:** Please replace `<user>` with your (Windows) username (e.g. `rene`)

   Save the file and exit `nano`:

   1. <kbd>Ctrl</kbd> + <kbd>O</kbd>
   2. <kbd>⏎</kbd>
   3. <kbd>Ctrl</kbd> + <kbd>X</kbd>)

10. Restart WSL: See step `8`

11. Install `usbipd` (Windows Shell):

    ```pwsh
    winget install usbipd
    ```

12. Attach CAN-Adapter to Linux VM (Windows Shell)

    ```pwsh
    usbipd wsl list
    # …
    # 5-3    0c72:0012  PCAN-USB FD                      Not attached
    # …
    usbipd wsl attach -d CANbuntu --busid 5-3
    usbipd wsl list
    # …
    # 5-3    0c72:0012  PCAN-USB FD                      Attached - CANbuntu
    # …
    ```

13. Check for PEAK CAN adapter in Linux (Optional, Linux Shell):

    ```sh
    dmesg | grep peak_usb
    # …
    # peak_usb 1-1:1.0: PEAK-System PCAN-USB FD v1 fw v3.2.0 (1 channels)
    # …

    lsusb
    # …
    # Bus 001 Device 002: ID 0c72:0012 PEAK System PCAN-USB FD
    # …
    ```

14. Add virtual link for CAN device (Linux Shell)

    ```sh
    sudo ip link set can0 type can bitrate 1000000
    sudo ip link set can0 up
    ```

    > **Note**: If the commands above fail with the error message:
    >
    > > RTNETLINK answers: Connection timed out
    >
    > then please disconnect and connect the USB CAN adapter. After that attach it to the Linux VM again (see step `12`).

15. Install `pip` (Linux Shell):

    ```sh
    sudo apt install -y python3-pip
    ```

16. Install ICOc (Linux Shell)

    ```sh
    cd ~
    mkdir Documents
    cd Documents
    git clone https://github.com/MyTooliT/ICOc.git
    cd ICOc
    python3 -m pip install --prefix=$(python3 -m site --user-base) -e .
    ```

17. Run a script to test that everything works as expected (Linux Shell)

    ```sh
    icon list
    ```

    If the command above fails with the message

    ```
    Command 'icon' not found…
    ```

    then you might have to logout and login into the WSL session again before you execute `icon list` again.

> **Notes:**
>
> - You only need to repeat steps
> - `12`: attach the CAN adapter to the VM in Windows and
> - `14`: create the link for the CAN device in Linux
>
> after you set up everything properly once.
>
> - Unfortunately [configuring the CAN interface automatically](#introduction:section:pcan-driver:linux) does not seem to work (reliably) on WSL yet

### Installing/Using Simplicity Commander

1. Download and unpack [Simplicity Commander](https://community.silabs.com/s/article/simplicity-commander?language=en_US) (Linux Shell)

   ```sh
   sudo apt install -y unzip
   mkdir -p ~/Downloads
   cd ~/Downloads
   wget https://www.silabs.com/documents/public/software/SimplicityCommander-Linux.zip
   unzip SimplicityCommander-Linux.zip
   cd SimplicityCommander-Linux
   tar xf Commander_linux_*.tar.bz
   mkdir -p ~/Applications
   mv commander ~/Applications
   # Fix J-Link connection
   # https://wiki.segger.com/J-Link_cannot_connect_to_the_CPU
   sudo cp ~/Applications/commander/99-jlink.rules /etc/udev/rules.d/
   ```

2. Add `commander` binary to path (Linux Shell)

   1. Open `~/.profile` in `nano`:

      ```sh
      nano ~/.profile
      ```

   2. Add the following text at the bottom:

      ```sh
      if [ -d "$HOME/Applications/commander" ] ; then
          PATH="$HOME/Applications/commander:$PATH"
      fi
      ```

   3. Save your changes

3. Restart WSL
4. Connect programming adapter to Linux (Windows Shell)

   ```pwsh
   usbipd wsl list
   # …
   # 5-4    1366:0105  JLink CDC UART Port (COM3), J-Link driver Not attached
   # …
   usbipd wsl attach --busid 5-4
   ```

5. Check if `commander` JLink connection works without using `sudo` (Linux Shell)

   ```sh
   commander adapter dbgmode OUT --serialno <serialnumber>
   # Setting debug mode to OUT...
   # DONE
   ```

   Notes:

   - Please replace `<serialnumber>` with the serial number of your programming board (e.g. `440069950`):

     ```sh
     commander adapter dbgmode OUT --serialno 440069950
     ```

   - If the command above [fails with the error message](https://stackoverflow.com/questions/55313610/importerror-libgl-so-1-cannot-open-shared-object-file-no-such-file-or-directo):

     ```
     error while loading shared libraries: libGL.so.1: cannot open shared object file…
     ```

     then you need to install `libgl1`:

     ```
     sudo apt install -y libgl1
     ```

### Run Tests in WSL

**Note:** The tests use the command-line `xdg-open`. For the tests also work on Linux, then you need to install the Python package [`xdg-open-wsl`](https://github.com/cpbotha/xdg-open-wsl):

```
pip3 install --user git+https://github.com/cpbotha/xdg-open-wsl.git
```

1. Start WSL (Windows Shell)

   ```sh
   wsl -d CANbuntu --cd "~/Documents/ICOc"
   ```

2. Connect programming/CAN adapter to Linux (Windows Shell):

   ```sh
   $jlink_id = usbipd wsl list | Select-String JLink | %{$_ -replace '(\d-\d).*','$1'}
   $can_id = usbipd wsl list | Select-String PCAN-USB | %{$_ -replace '(\d-\d).*','$1'}
   usbipd wsl attach -d CANbuntu --busid $jlink_id
   usbipd wsl attach -d CANbuntu --busid $can_id
   ```

3. Configure CAN interface (Linux Shell):

   ```sh
   sudo ip link set can0 type can bitrate 1000000
   sudo ip link set can0 up
   ```

4. Run tests (Linux Shell):

   ```sh
   make run
   ```

## Docker on Linux

The text below shows how you can use (code of) the new Network class in a Docker container on a **Linux host**. The description on how to move the interface of the Docker container is an adaption of an [article/video from the “Chemnitzer Linux-Tage”](https://chemnitzer.linux-tage.de/2021/de/programm/beitrag/210). Currently we provide two images based on:

- [Alpine](https://hub.docker.com/r/mytoolit/icoc-alpine) and
- [Ubuntu](https://hub.docker.com/r/mytoolit/icoc-ubuntu).

### Pull the Docker Image

You can download a recent version of the image from Docker Hub

- for Alpine:

```
docker image pull mytoolit/icoc-alpine:latest
```

- or Ubuntu:

```
docker image pull mytoolit/icoc-ubuntu:latest
```

### Build the Docker Image

If you **do not want to use the prebuilt image**, then you can use the commands below (in the root of the repository) to build them yourself:

- Alpine Linux:

```sh
docker build -t mytoolit/icoc-alpine -f Docker/Alpine/Dockerfile .
```

- Ubuntu:

```sh
docker build -t mytoolit/icoc-ubuntu -f Docker/Ubuntu/Dockerfile .
```

### Using ICOc in the Docker Container

1. Run the container **(Terminal 1)**

   1. Open a new terminal window

   2. Depending on the Docker container you want to use please execute one of the following commands:

      - Alpine:

        ```sh
        docker run --rm -it --name icoc mytoolit/icoc-alpine
        ```

      - Ubuntu:

        ```sh
        docker run --rm -it --name icoc mytoolit/icoc-ubuntu
        ```

2. Make sure the CAN interface is available on the Linux host **(Terminal 2)**

   1. Open a new terminal window
   2. Check that the following command:

      ```sh
      networkctl list
      ```

      lists `can0` under the column `LINK`

3. Move the CAN interface into the network space of the Docker container **(Terminal 2)**

   ```sh
   export DOCKERPID="$(docker inspect -f '{{ .State.Pid }}' icoc)"
   sudo ip link set can0 netns "$DOCKERPID"
   sudo nsenter -t "$DOCKERPID" -n ip link set can0 type can bitrate 1000000
   sudo nsenter -t "$DOCKERPID" -n ip link set can0 up
   ```

4. Run a test command in Docker container **(Terminal 1)** e.g.:

   ```sh
   icon list
   ```

<a name="tutorials:section:updating-images-on-docker-hub"></a>

### Updating Images on Docker Hub

#### Preparation

If you have not done so already, you might have to [enable support for building Docker images for multiple architectures](https://cloudolife.com/2022/03/05/Infrastructure-as-Code-IaC/Container/Docker/Docker-buildx-support-multiple-architectures-images/):

1. Enable experimental features for the Docker daemon:

   1. Open `daemon.json`
   2. Set `"experimental"` to `true`

2. Create a builder (e.g. with name `builder`) and use it:

   ```sh
   docker buildx create --name builder --use
   ```

#### Update Steps

To update the official Docker images on Docker Hub, please use the steps below. All commands assume that you use a **POSIX shell** on a Unix system (e.g. Linux or macOS).

1. Login to Docker Hub

   ```
   printf '%s\n' "$ACCESS_TOKEN" | docker login -u mytoolit --password-stdin
   ```

   > **Note:** Please make sure that the variable `ACCESS_TOKEN` contains a valid [access token](https://hub.docker.com/settings/security)

2. Build and push the Docker images for multiple platforms:

   ```sh
   export ICOC_VERSION="$(cat mytoolit/__init__.py |
                          sed -E 's/__version__ = "([0-9]+\.[0-9]+\.[0-9]+)"/\1/')"
   docker buildx build \
     --platform linux/amd64,linux/arm64 \
     -t mytoolit/icoc-alpine \
     -t mytoolit/icoc-alpine:stable \
     -t "mytoolit/icoc-alpine:$ICOC_VERSION" \
     -f Docker/Alpine/Dockerfile \
     --push .
   docker buildx build \
     --platform linux/amd64,linux/arm64 \
     -t mytoolit/icoc-ubuntu \
     -t mytoolit/icoc-ubuntu:stable \
     -t "mytoolit/icoc-ubuntu:$ICOC_VERSION" \
     -f Docker/Ubuntu/Dockerfile \
     --push .
   ```
