import pronouncing
import wn
import random
import numpy as np
import pickle
from collections import defaultdict

# grab word and vowel data from pickles
with open("wordnet_words_1.4.pkl", "rb") as f:
    words = pickle.load(f)

with open("vowel_counts.pkl", "rb") as f:
    vowel_counts = pickle.load(f)

vowel_counts_grouped = {}
sanitized_words = [s for s in words if " " not in s]

with open("wordnet_words_1.4.pkl", "wb") as f:
    pickle.dump(words, f)

with open("vowel_counts.pkl", "wb") as f:
    pickle.dump(vowel_counts, f)

def word_map():

    if wn.lexicons():
        # print("Some lexicon(s) installed")
        # print(f"lexicons: {wn.lexicons()}  num wordnets: {len(wn.words())}\n")
        lexicon = wn.Wordnet('omw-en:1.4')

    else:
        # print("No lexicons installed — need to download.")
        # Download lexicons if they don't exist yet
        wn.download('omw-en')

    # Get synset
    synsets = list(wn.Wordnet().synsets())

    syn = random.choice(synsets)

    map = {}
    for x in range(len(sanitized_words)):
        # print(sanitized_words[x])
        try:
            map[sanitized_words[x]] = distinct_vowels(sanitized_words[x])
        except IndexError as e:
            # print(sanitized_words[x])
            print(e)

    print(map)



def distinct_vowels(word=""):

    phonemes = pronouncing.phones_for_word(word)

    vowels = {"AA","AE","AH","AO","AW",
                        "AY","EH","ER","EY","IH",
                        "IY","OW","OY","UH","UW"}

    vowel_count = 0
    phonemes = phonemes[0].split()
    for phoneme in phonemes:
        if phoneme[:2] in vowels:
            vowel_count+=1

    # return print(f"word: {word} \n vowels: {vowel_count} \n phonemes: {phonemes}")
    return vowel_count




def generate_freestyle(bar=""):

    with open("vowel_counts_grouped.pkl", "rb") as f:
        vowel_counts_grouped = pickle.load(f)
    
    words = bar.split(" ")
    new_bar = ""
    for word in words:
        # print(f"word: {word}, value: {distinct_vowels(word)}")
        new_bar += " " + random.choice(vowel_counts_grouped[distinct_vowels(word)])

    print(new_bar)



generate_freestyle("Some shit just cringe worthy I don't even gotta say it I guess")