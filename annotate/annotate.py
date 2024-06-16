from db.connect import query

def annotate():
    unlabeled_data = query()
    print("""Hello, thank you for your willingness to annotate the data!\n
                Below you'll be given sentences in its original form and its simplified form.\n
                Type 'y' if the simplified form looks good to you, 
                'n' if it doesn't (you'll be then asked to rewrite it), 
                's' to skip the sentence, and
                'q' to quit annotating.\n\n""")
    while True:
        print("Please evaluate the following sentence pairs:")
        for pair in unlabeled_data:
            while True:
                print(f"Original: {pair['original']} \nSimplified: {pair['simplified']}")
                annotation = input("Does the simplified form look good? (y/n/s/q): ")
                if annotation == 'y':
                    break
                elif annotation == 'n':
                    simplified = input("Please rewrite the simplified form: ")
                    pair[2] = simplified
                    break
                elif annotation == 's':
                    break
                elif annotation == 'q':
                    return
                else:
                    print("Invalid input. Please try again.") 


def main():
    annotate()

if __name__ == '__main__':
    main()