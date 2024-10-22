# joke_response.py
import random

# Sample jokes list
JOKES = [
    "Why don't scientists trust atoms? \n \n Because they make up everything!😆",
    "Why did the math book look sad? \n \n Because it had too many problems.🤣",
    "Why can't you give Elsa a balloon? \n \n Because she will let it go!😆",
    "What do you call fake spaghetti? \n \n An impasta!😆",
    "Why don't skeletons fight each other? \n \n They don't have the guts.🤣",
    "What did one plate say to the other plate? \n \n Lunch is on me!😆",
    "Why did the scarecrow win an award? \n \n Because he was outstanding in his field!🤣",
    "What do you get when you cross a snowman and a vampire? \n \n Frostbite!😆",
    "Why did the bicycle fall over? \n \n Because it was two-tired!🤣",
    "What’s orange and sounds like a parrot? \n \n A carrot!😆",
    "Why can't your nose be 12 inches long? \n \n Because then it would be a foot!🤣",
    "Why don't eggs tell jokes? \n \n They'd crack each other up!😆",
    "What do you call a factory that makes good products? \n \n A satisfactory!🤣",
    "Why did the golfer bring two pairs of pants? \n \n In case he got a hole in one!😆",
    "What do you call cheese that isn't yours? \n \n Nacho cheese!🤣",
    "Why did the computer go to the doctor? \n \n Because it had a virus!😆",
    "Why was the math book always stressed? \n \n It had too many problems!🤣",
    "What did the ocean say to the beach? \n \n Nothing, it just waved!😆",
    "Why don’t some couples go to the gym? \n \n Because some relationships don’t work out!😆",
    "What do you call a bear with no teeth? \n \n A gummy bear!🤣"
]

# Get a random joke that hasn't been told yet
def get_random_joke(jokes_told):
    available_jokes = [joke for joke in JOKES if joke not in jokes_told]
    if not available_jokes:
        return None  # No jokes left to tell
    return random.choice(available_jokes)

# Function to generate a joke response
def get_joke_response(context):
    jokes_told = context.get('jokes_told', [])

    # Get a random joke
    next_joke = get_random_joke(jokes_told)

    if next_joke:
        jokes_told.append(next_joke)
        context['jokes_told'] = jokes_told  # Save the updated list to context
        return next_joke + "\n\nWould you like to hear another joke?"
    else:
        # No more jokes available
        return "Sorry, I've told all my jokes! Let's talk about something else."
