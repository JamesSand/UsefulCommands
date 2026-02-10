

### cursor tunnel

#### Step1: install cursor tunnel on server

```bash
# For Linux ARM architecture, install with the following command
curl -Lk 'https://api2.cursor.sh/updates/download-latest?os=cli-alpine-arm64' -o cursor_cli.tar.gz

# For x86_64 architecture: this one works
curl -Lk 'https://api2.cursor.sh/updates/download-latest?os=cli-alpine-x64' -o cursor_cli.tar.gz

tar -xzf cursor_cli.tar.gz

# Start the tunnel
cursor tunnel
```



#### Step2: install tunnel extension in IDE

> I've seen on the Cursor forum that this method has a certain probability of failure. If the installation fails, don't waste time on cursor tunnel - try other methods instead.

The next step is to install the tunnel extension in Cursor, but Cursor's marketplace has removed the remote tunnel extension... You need to install it manually.

Step one: Download the remote tunnel vsix file from **VSCode** to your local computer

![image-20260209233845925](./imgs/image-20260209233845925.png)

You will then get a file like this

![image-20260209234255494](./imgs/image-20260209234255494.png)





Step two: Install this vsix file in Cursor

You need to install it via command line

Press Ctrl + Shift + P to open Cursor's command palette

Then type

```
Extensions: Install from VSIX...
```





Step three: Use the tunnel extension to connect to the server

You also need to use the command line to connect. For some reason, the tunnel doesn't appear in the remote explorer.

Press Ctrl + Shift + P to open Cursor's command palette

Then type

```
Remote-Tunnels: Connect to Tunnel...
```



However, note that the first time you connect, the server download may freeze. This appears to be because Cursor blocks this process. In this case, you need to restart Cursor, and then you should be able to connect to the tunnel normally.









