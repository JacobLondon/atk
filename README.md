# ATK
Any number of players may be ships, any number of players may spawn enemies. Run `server.py` before running any `atk.py` instance.

# Example
Two 'good' players and two 'bad' players. Over the network, so all players see all other players. See `settings.json` for setting IP addresses, port numbers, and which kind of player to be. Utilizes my Pyfs utility idea where users can read/write to a file descriptor which in this case is bound to a TCP/IP file server. ESC or X button to quit. Disconnected players disappear from all other active clients and server.

Bad players spawn enemies, and good players shoot enemies. Last one standing wins!

![Screenshot](https://user-images.githubusercontent.com/17059471/126906515-500a4f46-a830-4b83-bac8-f7d5c27175d6.png)

Good:
* Move with mouse
* Shoot with spacebar, not getting hit makes attacks shoot more.

Bad:
* Spawn enemy with mouse and spacebar in the top half of the screen.
* Set enemy move type with 1: motionless, 2: down, 3: weave, 4: down-left, 5: down-right.
* Set enemy shoot type with q: single, w: double, e: triple, r: sides, t: star, y: spiral.
