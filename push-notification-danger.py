import pushbullet
apiKey="XXXXXX" #withheld from Git repository

pb=pushbullet.Pushbullet(apiKey)
push=pb.push_note("Vehicle occupant in danger!", "An occupant you left behind is being subjected to dangerous conditions.")
