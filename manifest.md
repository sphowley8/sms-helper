Purpose
- Reduce time clicking into and clicking through apps on your phone. By outsourcing common tasks to sms, I am aiming to prevent myself from getting caught in dopamine/distraction traps
- I often send myself little notes/todo lists/etc via text because it is the quickest app to open and doesn't send me down a rabbit hole or cause me to think about anything else. It is just a notepad. But this is rudimentary -- rather, I would like to be able to send a text with the following, and it will file my note in github in a file called "todo.md" with the content of my list
    - 'notes add/todo -water plants -safeway -send email'
- The minimal viable product for this application is to create an sms reciever that I can text, it will take the payload of the body of my text and send it to a lambda function, the lambda function will parse the payload and perform the function accordingly, in this case, it will commit an appendation to the todo.md file.
- In the future, i may want to have functionality to allow me to clean notes, retrieve notes, create an activity on strava, or add an event to my calendar

How it will work
- Text sms endpoint --> SMS endpoint forwards body of text to lambda --> lambda parses text according to following rules
    - function action/target/
      - function -- the function (notes, calendar, strava)
      - action -- the action ()
      - target -- the target of the action on (notes file, calendar nmae, strava identifier)
- To start, we will ONLY be focusing on the most basic notes functionality 
    - Send a text with the above format. If the file with the target name exists, append the note to it. If the file does not exist, create <target>.md and add the note to it
    - Send a "Got it, updated" text if it works
    - Send a "Dah, something got messed up. Some details are below: <Details on newline>" message if it does not work"
