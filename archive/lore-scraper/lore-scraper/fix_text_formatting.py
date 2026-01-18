import json
import os
import re
from pathlib import Path

# Configuration
LORE_DIR = Path(r"c:\esp32-project\lore\fallout76_canon\entities")

# Regex Compilation
CITATION_REGEX = re.compile(r'\[\d+\]')
CAMEL_CASE_REGEX = re.compile(r'([a-z])([A-Z])') # e.g., "WalkerLiving" -> "Walker Living" (Already in scraper but good to re-run)

# Logic to split "word1word2" where word2 is a common stopword or connector
# We are looking for [lowercase letter][keyword_starting_with_lowercase]
# Keywords that commonly follow other words without space due to scraper error
KEYWORDS = [
    'was', 'is', 'are', 'were', 'has', 'had', 'have',
    'in', 'at', 'on', 'to', 'from', 'for', 'with', 'by', 'near',
    'and', 'but', 'or', 'nor',
    'the', 'a', 'an',
    'this', 'that', 'these', 'those',
    'his', 'her', 'their', 'its',
    'prior', 'during', 'after', 'before', 'since',
    'living', 'serving', 'located', 'associated', 'also', 'believed', 'known',
    'alongside', 'outside', 'inside'
]

# Construct a regex like: ([a-z])(was|is|are|...)\b
# But we must be careful. "sand" -> "s and".
# We only want to split if the preceding part looks like a complete word? 
# No, "Davewas" -> "Dave" is a word. "sand" -> "s" is a letter.
# Most scraper errors happen at the boundary of a link.
# e.g. "Walker[Link]living" -> "Walkerliving". "Walker" is a capitalized name usually.
# "Appalachia[Link]prior" -> "Appalachiaprior".
# "Queen[Link]and" -> "Queenand".
# "Mirelurk[Link]Dave" -> "MirelurkDave" (Caught by camelCase regex)
# "plague,[1][2]Dave" -> "plague,Dave" (Caught by punctuation regex?)

# Let's target the specific "End of word + Common Start Word" pattern.
# We can't distinguish "sand" from "s and" purely by regex without a dictionary.
# However, "was", "is" often follow proper nouns in these descriptions.
# "Davewas" -> "Dave" (Proper) + "was".
# "Walkerliving" -> "lker" + "living".
# If I check if the preceding character is standard lowercase, it's risky for general words.
# BUT, looking at the grep results: "Garrahanwas", "Woodwas", "Alawas", "Transmissionis".
# These are ALL capitalized words (names) merging into lowercase keywords.
# So: ([A-Za-z]+)([a-z]+) ?
# No, "Garrahanwas" -> "n" + "was".
# Strategy: Only split if the "keyword" is NOT a valid suffix for the preceding text?
# Too complex.
# Strategy: Only fix the VERY common ones that are safe?
# "was" -> "twas"? No. "iwas"? No.
# "is" -> "his", "this", "miss", "axis", "basis". "is" is DANGEROUS to split.
# "and" -> "sand", "band", "land", "hand". "and" is DANGEROUS.
# "in" -> "bin", "sin", "thin", "win". DANGEROUS.
# "at" -> "cat", "bat", "hat". DANGEROUS.

# Wait, `get_text(separator=' ')` is the *correct* fix.
# Parsing "Davewas" without re-scraping is hard.
# However, "Davewas" might be fixable if we assume the previous word ends in a specific way?
# No.

# Alternative Strategy:
# Focus on the known failures involving Punctuation and Citations.
# 1. `[1]word` -> `[1] word` (or remove [1])
# 2. `word[1]` -> `word [1]` (or remove [1])
# 3. `word,word` -> `word, word`
# 4. `word.word` -> `word. word`
# 5. `)word` -> `) word`
# 6. `word(` -> `word (`

def fix_formatting(text):
    if not text:
        return text
        
    original = text
    
    # 1. Remove citations entirely [1], [12]
    text = CITATION_REGEX.sub('', text)
    
    # 2. Fix missing space after punctuation
    # "2102.After" -> "2102. After"
    # "Plague,Dave" -> "Plague, Dave"
    text = re.sub(r'([.,;?!])([A-Za-z])', r'\1 \2', text)
    
    # 3. Fix missing space around parens
    # "(Alex)is" -> "(Alex) is"
    # "Walker(living" -> "Walker (living"
    text = re.sub(r'(\))([A-Za-z])', r'\1 \2', text)
    text = re.sub(r'([a-z])(\()', r'\1 \2', text)
    
    # 4. Fix missing space in CamelCase (already in scraper but good here)
    # "MirelurkDave" -> "Mirelurk Dave"
    text = CAMEL_CASE_REGEX.sub(r'\1 \2', text)
    
    # 5. Fix "digitsWord" or "wordDigits"
    # "to2102" -> "to 2102"
    # "2102Dave" -> "2102 Dave"
    text = re.sub(r'([a-z])(\d)', r'\1 \2', text)
    text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', text)

    # 6. Safe Keyword Splitting
    # Only split specific keywords that are rarely suffixes
    # "prior" -> "Appalachiaprior". "superior"? "interior"? "warrior"? 
    # "living" -> "Walkerliving". "forgiving"? "reliving"?
    # "located" -> "Shacklocated". "dislocated"?
    # Maybe limit to capitalized preceding words? "AppalachiaPrior" (no, it's lower).
    # If we restrict to: [A-Z][a-z]+keyword
    # "Davewas" -> [A-Z]ave + was.
    # "Alawas" -> [A-Z]la + was.
    # "Woodwas" -> [A-Z]ood + was.
    # "Walkerliving" -> [A-Z]alker + living.
    # "Appallachiaprior" -> [A-Z]ppallachia + prior.
    
    # Heuristic: [A-Z][a-z]+(was|is|in|at|to|for|with|and|the)
    # Be careful of "This", "That". 
    # "This" -> Th + is? No. [A-Z]h + is. "This" starts with T.
    # "His" -> [A-Z] + is. H + is.
    # "Davis" -> [A-Z]av + is. (Name Davis).
    # "Lewis" -> [A-Z]ew + is. (Name Lewis).
    # "Morris" -> [A-Z]orr + is.
    # "Paris" -> [A-Z]ar + is.
    # "Travis" -> [A-Z]rav + is.
    # So "is" is NOT safe even with Capitalized word check. (Davis, Lewis, Travis).
    
    # "was": "Dwlas"? No. "Twas"? No.
    # "Davewas" -> safe? 
    # Are there names ending in 'was'? "Kiwas"? "Siwas"? 
    # It seems "was" is RELATIVELY safe to split if preceding is > 2 chars?
    # regex: ([A-Z][a-z]{2,})(was)\b
    text = re.sub(r'([A-Z][a-z]{2,})(was)\b', r'\1 \2', text)
    
    # "in": "Kevin"? "Franklin"? "Berlin"? "Martin"?
    # DANGEROUS.
    
    # "and": "Ferdinand"? "Roland"? "Poland"? "Brand"? "Grand"?
    # DANGEROUS.
    
    # "prior": "Superior"? "Interior"?
    # DANGEROUS.
    
    # Conclusion: Don't guess too much on lowercase merges in this script.
    # Just fix the structural ones (punctuation/digits/brackets).
    
    return text

def main():
    count = 0
    modified = 0
    
    for text_file in LORE_DIR.rglob("*.json"):
        count += 1
        try:
            with open(text_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            original_desc = data.get('description', '')
            if not original_desc:
                continue
                
            new_desc = fix_formatting(original_desc)
            
            if new_desc != original_desc:
                data['description'] = new_desc
                # Update verification since we touched it
                if 'verification' in data:
                    data['verification']['last_verified'] = "2026-01-10"
                    data['verification']['formatting_fixed'] = True
                
                with open(text_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                modified += 1
                # print(f"Fixed: {text_file.name}")
                
        except Exception as e:
            print(f"Error processing {text_file}: {e}")
            
    print(f"Scanned {count} files. Modified {modified} files.")

if __name__ == "__main__":
    main()
