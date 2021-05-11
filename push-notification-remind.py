import pushbullet
apiKey="XXXXXXX" #withheld from Git repository

pb=pushbullet.Pushbullet(apiKey)
push=pb.push_note("You left someone behind!", "Occupant detected in your vehicle.")
