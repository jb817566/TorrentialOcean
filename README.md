# TorrentialOcean
Temporarily spins up a droplet to download a torrent, grab the files, and then slurps them down from the droplet

This project uses Python2

# Usage:
1. Install any necessary requirements with `pip install -r requirements.txt`
2. Configure with the `config.json` file to your liking. If you don't want to put it in the config file, you can also set the DO_TOKEN environment variable with:  
 `export DO_TOKEN=[YOUR DO TOKEN]`
3. Run `python main.py [Torrent Link or Magnet Link]`
4. Killing with `Ctrl-C` will also destroy the droplet to clean up

### How it works
1. Generates a keypair to be used to authenticate with a droplet
2. Uses a DigitalOcean API Secret Token in order to spin up a droplet on your behalf according to your specifications
3. SSHs into the droplet using the private key
4. Installs `aria2` on the droplet, which is a command-line tool used to download files with a bunch of protocols like HTTP/S, FTP, SFTP, BitTorrent, and Magnet
5. Prints the current output from the server's CLI
6. Securely downloads the file to your local machine through SSH's encryption
7. Cleans up resources by destroying the current droplet when `Ctrl-C` is pressed or when you completely download the files