# Core python/encoding
import unicodedata
from unidecode import unidecode
import difflib
import re
import html

# NLTK Imports
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet

# Download the words corpus if you haven't already
nltk.download("words")
nltk.download("wordnet")

###############################################################################
# global constants
###############################################################################
AUTHOR_SEP = ","
SMAP = {
    "’": "'",
    "–": "-",
    "”": '"',
    "“": '"',
    "ˈ": "'",
    "−": "-",
    "—": "-",
    "‘": "'",
    "\xa0": " ",
    "∼": "~",
    "u ̈": "ü",
    "ﬁ": "fi",
    "ﬂ": "fl",
    "\\%": "%",
    "\\&": "&",
    "\\_": "_",
    "’": "'",
    "‘": "'",
    "`": "'",
}
SUBS = [
    ("’", "'"),
    ("\n", " "),
    ("- ", "-"),
    # ("-", ""),
    ("\\%", "%"),
    ("\\&", "&"),
    ("  ", " "),
    ("\\_", "_"),
]
HYPHONATED_WORDS = {
    # Machine Learning
    "self-attention",
    "state-of-the-art",
    "decision-tree",
    "deep-learning",
    "reinforcement-learning",
    "multi-task",
    "cross-validation",
    "transfer-learning",
    "under-fitting",
    "over-fitting",
    "fine-tuning",
    "feature-extraction",
    "k-nearest-neighbors",
    "k-means",
    "support-vector-machine",
    "hyper-parameter",
    "zero-shot",
    "one-shot",
    "semi-supervised",
    "unsupervised-learning",
    "neural-network",
    "convolutional-neural-network",
    "recurrent-neural-network",
    "long-short-term-memory",
    "gradient-descent",
    "back-propagation",
    "random-forest",
    "ensemble-learning",
    "generative-adversarial-network",
    "vanishing-gradient",
    "batch-normalization",
    "auto-encoder",
    "principal-component-analysis",
    # Speech Science
    "articulatory-phonetics",
    "acoustic-phonetics",
    "psychoacoustic-model",
    "vowel-quality",
    "place-of-articulation",
    "manner-of-articulation",
    "co-articulation",
    "speech-perception",
    "formant-frequency",
    "voice-onset-time",
    "pitch-accent",
    "syllable-structure",
    "suprasegmental-feature",
    "intonation-pattern",
    "spectral-analysis",
    "spectral-envelope",
    "spectral-slope",
    "harmonic-to-noise-ratio",
    "frequency-domain",
    "time-domain",
    "spectral-density",
    "spectral-flatness",
    "spectral-centroid",
    "power-spectrum",
    "energy-envelope",
    "zero-crossing-rate",
    "formant-tracking",
    "bandwidth-narrowing",
    "cepstral-coefficients",
    "mel-frequency-cepstral-coefficients",
    "short-time-fourier-transform",
    "linear-predictive-coding",
    "minimum-phase",
    # Speech Technology
    "text-to-speech",
    "speech-to-text",
    "automatic-speech-recognition",
    "speaker-verification",
    "speaker-identification",
    "voice-activity-detection",
    "noise-reduction",
    "speech-enhancement",
    "voice-controlled",
    "voice-user-interface",
    "language-model",
    "phoneme-recognition",
    "word-error-rate",
    "phrase-error-rate",
    "signal-to-noise-ratio",
    "human-computer-interaction",
    "real-time-processing",
    "end-to-end",
    "voice-synthesis",
    "prosody-modeling",
    "pitch-tracking",
    "speech-synthesis",
    "audio-descriptor",
    "keyword-spotting",
    "emotion-recognition",
    "sentiment-analysis",
    "natural-language-processing",
    "domain-adaptation",
    "multi-modal",
    "context-aware",
    "wake-word",
    "acoustic-model",
}
NON_HYPHENATED_WORDS = [
    # Speech Science
    "speech",
    "phonetic",
    "acoustic",
    "prosody",
    "intonation",
    "pitch",
    "stress",
    "morphology",
    "syntax",
    "pragmatics",
    "discourse",
    "analysis",
    "phonology",
    "articulation",
    "phoneme",
    "syllable",
    "vowel",
    "consonant",
    "spectrogram",
    "formants",
    "harmonic",
    "frequency",
    "amplitude",
    "resonance",
    "voice",
    "timbre",
    "nasality",
    "voicing",
    "plosive",
    "fricative",
    "affricate",
    "glottis",
    "larynx",
    "suprasegmental",
    "coarticulation",
    "utterance",
    "diacritic",
    "allophone",
    "phonotactics",
    "juncture",
    "paralinguistic",
    "intonational",
    "phonotactic",
    "prosodic",
    "acoustics",
    "spectral",
    "fundamental",
    "frequency",
    "vocal",
    "tract",
    "speech",
    "production",
    "speech",
    "perception",
    "audiology",
    "speech",
    "pathology",
    "cognition",
    "neurolinguistics",
    "psycholinguistics",
    "language",
    "processing",
    "sensorimotor",
    "coordination",
    "speech",
    "development",
    "speech",
    "disorder",
    "aphasia",
    "dysarthria",
    "stuttering",
    "apraxia",
    "language",
    "acquisition",
    # Speech Technology
    "recognition",
    "transcription",
    "synthesis",
    "automatic",
    "speech",
    "recognition",
    "signal",
    "processing",
    "formant",
    "synthesis",
    "concatenative",
    "synthesis",
    "parametric",
    "synthesis",
    "speech",
    "enhancement",
    "speech",
    "separation",
    "speech",
    "denoising",
    "speech",
    "coding",
    "voice",
    "activity",
    "detection",
    "speaker",
    "identification",
    "speaker",
    "verification",
    "speaker",
    "diarization",
    "language",
    "modeling",
    "acoustic",
    "modeling",
    "pronunciation",
    "modeling",
    "language",
    "understanding",
    "keyword",
    "spotting",
    "dialogue",
    "system",
    "interactive",
    "voice",
    "response",
    "system",
    "natural",
    "language",
    "understanding",
    "natural",
    "language",
    "generation",
    "speech-to-text",
    "speech",
    "recognition",
    "voice",
    "assistant",
    "speech",
    "interface",
    "emotion",
    "recognition",
    "sentiment",
    "analysis",
    "speech",
    "translation",
    "prosody",
    "modification",
    "voice",
    "conversion",
    "vocal",
    "biometrics",
    "speaker",
    "adaptation",
    "deep",
    "learning",
    "in",
    "speech",
    "technology",
    "recurrent",
    "neural",
    "network",
    "in",
    "speech",
    "processing",
    "hidden",
    "markov",
    "model",
    "in",
    "speech",
    "recognition",
    "language",
    "identification",
    "multilingual",
    "speech",
    "processing"
    # Artificial Intelligence
    "artificial",
    "intelligence",
    "model",
    "algorithm",
    "neural",
    "network",
    "deep",
    "learning",
    "supervised",
    "unsupervised",
    "reinforcement",
    "optimization",
    "prediction",
    "inference",
    "training",
    "validation",
    "testing",
    "hyperparameter",
    "backpropagation",
    "gradient",
    "descent",
    "activation",
    "function",
    "layer",
    "attention",
    "encoder",
    "decoder",
    "sequence",
    "generation",
    "normalization",
    "regularization",
    "overfitting",
    "underfitting",
    "epoch",
    "batch",
    "stochastic",
    "probabilistic",
    "bayesian",
    "turing",
    "test",
    "chatbot",
    "dialogue",
    "system",
    # Machine Learning
    "machine",
    "learning",
    "dataset",
    "feature",
    "extraction",
    "regression",
    "classification",
    "clustering",
    "segmentation",
    "detection",
    "parsing",
    "tokenization",
    "embedding",
    "vector",
    "dimensionality",
    "reduction",
    "representation",
    "corpus",
    "ontology",
    "semantic",
    "syntactic",
    "training",
    "validation",
    "testing",
    "modeling",
    "statistical",
    "generalization",
    "loss",
    "metric",
    "accuracy",
    "precision",
    "recall",
    "roc",
    "curve",
    "area",
    "confusion",
    "matrix",
    "true",
    "positive",
    "negative",
    "false",
    "binary",
    "logistic",
    "support",
    "vector",
    "neighbor",
    "decision",
    "tree",
    "random",
    "forest",
    "ensemble",
    "boosting",
    "bagging",
    "hierarchical",
    "cluster",
    "principal",
    "component",
    "analysis",
    "latent",
    "dirichlet",
    "allocation",
    "word",
    "embedding",
    "fasttext",
    "word2vec",
    "glove",
    "bert",
    "gpt",
    "transformer",
    "recurrent",
    "long",
    "memory",
    "gated",
    "unit",
    "encoder",
    "decoder",
    "architecture",
    "beam",
    "search",
    "greedy",
    "decoding",
    "attention",
    "mechanism",
    # Explainable AI
    "explainability",
    "explainable",
    "ai",
    "transparency",
    "interpretability",
    "accountability",
    "causality",
    "fairness",
    "bias",
    "model",
    "explanation",
    "decision",
    "rule",
    "traceability",
    "feature",
    "importance",
    "local",
    "global",
    "saliency",
    "map",
    "counterfactual",
    "example",
    "surrogate",
    "fidelity",
    "trust",
    "human",
    "rationale",
    "justification",
    "reasoning",
    "understandability",
    "clarity",
    "model",
    "confidence",
    "model",
    "debugging",
] + list(nltk.corpus.words.words())
LEMMATIZER = WordNetLemmatizer()
WORD_SET = set([LEMMATIZER.lemmatize(l.lower()) for l in NON_HYPHENATED_WORDS])


def slugify(value):
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")


def latexify(s: str, keep_space: bool = False) -> str:
    """Transform an input string to its LaTeX equivalent.

    Parameters
    ----------
    s: str
        The input string
    keep_space: bool
        Prevent the reduction of the amount of space
    Returns
    -------
    str
        the LaTeX version of the input string
    """
    for sym in ["_", "%", "&"]:
        s = s.replace(sym, "\\" + sym)
    if not keep_space:
        s = " ".join(s.split())
    return s


def norm_text(s: str, doslugify: bool = True, dolower: bool = False) -> str:
    """Helper to normalise any text.

    Parameters
    ----------
    s: str
        The text to normalise
    doslugify: boolean
        if true, then call slugify
    dolower: boolean
        if true then transform the input in lower case

    Returns
    -------
    str
        The normalised text
    """
    for x, y in SMAP.items():
        s = s.replace(x, y)
    if doslugify:
        s = slugify(s)
    if dolower:
        s = s.lower()
    return s.strip()


def split_name(fullname: str) -> tuple[str, str]:
    """Extract first name and second name from the input full name string

    Parameters
    ----------
    fullname : str
            fullname string

    Returns
    -------
    tuple[str, str]
            the tuple containing (firstname, lastname)
    """

    try:
        if "{" in fullname and "}" in fullname:
            nm1, rest = fullname.split("{")
            nm2, _ = rest.split("}")
        else:
            parts = fullname.split()
            nm1 = " ".join(parts[:-1])
            nm2 = parts[-1]
        return nm1.strip(), nm2.strip()
    except Exception as e:
        exit(f"problem parsing {fullname}: {e}")


def has_numbers(s: str) -> bool:
    """Helper to determine if the string contains a number

    Parameters
    ----------
    s : str
            the string to test

    Returns
    -------
    bool
            True if the string contains a number
    """
    return any(char.isdigit() for char in s)


def parse_authors(s: str) -> list[tuple[str, str]]:
    s = s.replace("  ", " ")
    auths = html.unescape(s).replace(",", " & ").replace(" and ", " & ").split("&")
    return [split_name(a.strip()) for a in auths if a.strip()]


def norm_authors(s: str) -> str:
    """Normalise the authors.

    Authors separated by ',' '*' signifies main author and remove any
    institutional info in parentheses.

    Parameters
    ----------
    s: str
        The author string

    Returns
    -------
    str
        The normalised author string
    """
    alist = []
    for a in s.split(AUTHOR_SEP):
        st = a.find("(")
        if st > -1:
            a = a[:st].strip()
        else:
            a = a.strip()

        # Get rid of curly braces used to identify last names
        a = a.replace("{", "").replace("}", "")
        alist += [a]

    return AUTHOR_SEP.join(alist).replace("*", "")


def convert_special_chars_to_ascii(text: str) -> str:
    """
    Converts special punctuation and marks in the text from UTF-8 to their ASCII equivalents,
    while leaving other characters (like accented letters) intact.

    Parameters:
    - text: str, the text containing UTF-8 special characters.

    Returns:
    - str: The text with special characters converted to ASCII.
    """

    def selective_unidecode(match):
        return unidecode(match.group(0))

    # Regex pattern to match special punctuation marks and symbols
    pattern = re.compile(r"[“”‘’«»„‚‹›—–…•·]", re.UNICODE)

    # Replace matches with their ASCII equivalents using unidecode
    return pattern.sub(selective_unidecode, text)


def norm_abstract(abstract: str, hyphenated_words: set[str] = HYPHONATED_WORDS) -> str:
    """
    Cleans the transcript of the abstract by removing unnecessary line breaks,
    joining split words, preserving specific hyphenated words, and converting
    UTF-8 punctuation to ASCII equivalents.

    Parameters:
    - pdf_abstract: str, the original abstract extracted from the PDF.
    - transcript: str, the transcript text of the abstract with potential line breaks and word splits.
    - hyphenated_words: set, a set of hyphenated words/phrases that should be preserved.

    Returns:
    - str: A cleaned and continuous version of the abstract.
    """

    # 1. Convert UTF-8 punctuation to ASCII equivalents
    abstract = convert_special_chars_to_ascii(abstract)
    abstract = abstract.replace("\n", " ")
    abstract = norm_text(abstract, False, False)

    # 2. Handle specific hyphenated words that should remain as is
    for word in hyphenated_words:
        pattern = word.replace("-", r"-\s*")  # e.g., self-attention -> self-\s*attention
        abstract = re.sub(pattern, word, abstract, flags=re.IGNORECASE)

    def is_valid_word(word):
        """
        Check if a word is valid by looking it up in the word set or using lemmatization.
        """
        return LEMMATIZER.lemmatize(word) in WORD_SET

    def fix_hyphenated(match):
        part1 = match.group(1)
        part2 = match.group(2)

        combined_word = part1 + part2

        # Check if the combined word or its lemma is valid
        if is_valid_word(combined_word.lower()):
            return combined_word
        else:
            return part1 + "-" + part2

    # 4. Handle hyphenated words at line breaks (excluding specific ones)
    abstract = re.sub(r"(\w+)-\s+(\w+)", fix_hyphenated, abstract)

    # 5. Remove any remaining extra newlines and leading/trailing whitespace
    abstract = re.sub(r"\s+", " ", abstract).strip()

    return abstract


def find_diffs(s1: str, s2: str, label_s1="-", label_s2="+") -> list[str]:
    """Helper to list the difference between two strings.

    Each string is split per sentence for better readability.

    Parameters
    ----------
    s1: str
        First string
    s2: str
        Second string
    label_s1: str
        Label of the first string
    label_s2: str
        Label of the second string

    Returns
    -------
    list[str]
        The list of differences prefixed with the string labels
    """
    # Split by punctuation to have a more refined comparison
    s1 = re.sub("[ \t]+", " ", s1)
    info1 = [f"{s}\n" for s in re.split(r"[.;:] ", s1)]
    info2 = [f"{s}\n" for s in re.split(r"[.;:] ", s2)]

    # Compute diff
    diff = difflib.ndiff(info1, info2)

    # Filter out equal lines
    final_diff = []
    for l in list(diff):
        if not l.startswith(" "):
            l = l.strip()
            if l.startswith("-"):
                l = label_s1 + l[1:]
            elif l.startswith("+"):
                l = label_s2 + l[1:]
            else:
                l = l[:1] + (" " * (len(label_s2) - 1)) + l[1:]
            final_diff.append(l)

    return final_diff


def escape_latex(text: str) -> str:
    """Escape LaTeX special characters."""
    replacements = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\^{}",
        "\\": r"\textbackslash{}",
    }
    return "".join(replacements.get(c, c) for c in text)


def diff_to_latex(s1: str, s2: str) -> str:
    sm = difflib.SequenceMatcher(None, s1, s2)
    result = []
    opt_codes = sm.get_opcodes()
    if (len(opt_codes) == 1) and (opt_codes[0][0] == "equal"):
        return ""

    for tag, i1, i2, j1, j2 in opt_codes:
        if tag == "equal":
            result.append(escape_latex(s1[i1:i2]))
        elif tag == "delete":
            result.append(r"\colorbox{red!20}{\sout{" + escape_latex(s1[i1:i2]) + "}}")
        elif tag == "insert":
            result.append(r"\colorbox{blue!20}{\underline{" + s2[j1:j2] + "}}")
        elif tag == "replace":
            result.append(r"\colorbox{red!20}{\sout{" + escape_latex(s1[i1:i2]) + "}}")
            result.append(r"\colorbox{blue!20}{\underline{" + s2[j1:j2] + "}}")

    return "".join(result)
