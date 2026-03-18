import math
from collections import defaultdict

def load_dataset(filepath):
    spam_messages = []
    ham_messages = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if not line:
                continue
            label, message = line.strip().split('\t', 1)
            if label == 'spam':
                spam_messages.append(message)
            else:
                ham_messages.append(message)
    return spam_messages, ham_messages

def compute_priors(spam_messages, ham_messages):
    n_spam = len(spam_messages)
    n_ham = len(ham_messages)
    n_total = n_ham + n_spam
    p_s = n_spam / n_total
    p_h = n_ham / n_total
    return n_spam, n_ham, p_s, p_h

def build_vocabulary(spam_messages, ham_messages):
    vocab = set()
    for msg in spam_messages + ham_messages:
        vocab.update(msg.lower().split())
    return vocab

def word_counts(messages):
    counts = defaultdict(int)
    for msg in messages:
        for w in set(msg.lower().split()):
            counts[w] += 1
    return counts

def laplace_likelihoods(counts, n_messages, vocab):
    vocab_size = len(vocab)
    return{
        w: (counts[w] + 1) / (n_messages + vocab_size)
        for w in vocab
    }

def classify_single_word(word, p_w_given_s, p_w_given_h, p_s, p_h):
    word = word.lower()
    if word not in p_w_given_s:
        return None, None, None
    p_w_s = p_w_given_s[word]
    p_w_h = p_w_given_h[word]

    p_w = p_w_s * p_s + p_w_h * p_h

    p_spam_given_w = (p_w_s * p_s)/p_w
    p_ham_given_w = (p_w_h * p_h)/p_w

    label = 'spam' if p_spam_given_w >= p_ham_given_w else 'ham'
    return p_spam_given_w, p_ham_given_w, label

def classify_message(words, p_w_given_s, p_w_given_h, p_s, p_h):
    log_p_spam = math.log(p_s)
    log_p_ham = math.log(p_h)

    for w in set(words):
        if w in p_w_given_s:
            log_p_spam += math.log(p_w_given_s[w])
            log_p_ham += math.log(p_w_given_h[w])
        
    label = 'spam' if log_p_spam >= log_p_ham else 'ham'
    return log_p_spam, log_p_ham, label

if __name__ == '__main__':
    spam_msgs, ham_msgs = load_dataset('C:/Users/rjwtu/OneDrive/Desktop/ChatBot/SMSSpamCollection')
    n_spam, n_ham, p_s, p_h = compute_priors(spam_msgs, ham_msgs)
    print(f'Dataset: {n_spam} spam, {n_ham} ham ({n_spam+n_ham} total)')

    print(f'P(Spam) = {p_s:.4f}  P(Ham) = {p_h:.4f}')
    print()

    vocab = build_vocabulary(spam_msgs, ham_msgs)
    spam_counts = word_counts(spam_msgs)
    ham_counts = word_counts(ham_msgs)
    P_w_given_S = laplace_likelihoods(spam_counts, n_spam, vocab)
    P_w_given_H = laplace_likelihoods(ham_counts, n_ham, vocab)
    print(f'Vocabulary size: {len(vocab)} words')
    print()


# Single-word classification for required test words
    test_words = ['sex', 'free', 'hello', 'call', 'meeting', 'urgent']
    print('Single-Word Classification Results')
    print('-' * 60)
    print(f'{"Word":<12} {"P(Spam|w)":>12} {"P(Ham|w)":>12} {"Decision":>10}')
    print('-' * 60)
    for word in test_words:
        p_s, p_h, label = classify_single_word(word, P_w_given_S, P_w_given_H, p_s, p_h)
        if label:
            print(f'{word:<12} {p_s:>12.6f} {p_h:>12.6f} {label:>10}')
        else:
            print(f'{word:<12} (not in training vocabulary)')
    print()
    # Multi-word classification example
    example_message = 'free offer call now win cash prize'
    words = example_message.lower().split()
    log_ps, log_ph, label = classify_message(words, P_w_given_S, P_w_given_H, p_s, p_h)
    print('Multi-Word Classification Example')
    print('-' * 60)
    print(f'Message : "{example_message}"')
    print(f'log P(Spam | message) = {log_ps:.4f}')
    print(f'log P(Ham | message) = {log_ph:.4f}')
    print(f'Decision : {label}')