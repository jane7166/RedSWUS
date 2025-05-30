# 기준 단어 리스트 (대문자 기준 130개)
reference_words = [
    "ALES", "ALGA", "ARCH", "AUNT", "AWAY",
    "BEAN", "BEEN", "BASE", "BOTH", "BANK",
    "CABS", "CAME", "CURV", "CITY", "CAMP",
    "DAZE", "DAMP", "DEFY", "DEED", "DECK",
    "EDEN", "ELSE", "ENDS", "EDGE", "EAST",
    "FARM", "FEAR", "FLIP", "FOUR", "FREE",
    "GLUE", "GOLF", "GUSH", "GOWN", "GRIM",
    "HAIL", "HARP", "HERO", "HUSH", "HOLY",
    "ICED", "IDOL", "ILLY", "ITCH", "IRIS",
    "JADE", "JOLT", "JURY", "JAVA", "JEST",
    "KECK", "KNIT", "KILO", "KEAR", "KASP",
    "LEAP", "LACE", "LEND", "LOUD", "LIFT",
    "MOCK", "MINI", "MINT", "MAIL", "MOVE",
    "NUTS", "NAVY", "NAPE", "NODS", "NURT",
    "OARS", "OGRE", "OMIN", "OPAL", "ONYX",
    "PLAY", "PICK", "PUSH", "PART", "PALM",
    "QUIZ", "QUIT", "QUAD", "QUEY", "QUID",
    "RUDE", "RARE", "RUBY", "RISE", "READ",
    "SUIT", "SWIM", "STAY", "SKIP", "SOUR",
    "TWIN", "TORN", "TEAR", "TAKE", "TALK",
    "UGLY", "UNDO", "USED", "UTAH", "USER",
    "VARY", "VAIN", "VEIL", "VENT", "VOTE",
    "WOVE", "WREN", "WARP", "WADE", "WIST",
    "XRAY", "XYST", "XIAN", "XERO", "XYLY",
    "YARD", "YOLK", "YAWN", "YULE", "YUCH",
    "ZITI", "ZONA", "ZERK", "ZIFF", "ZOBO"
]

# txt 파일에서 단어 불러오기 (중복 제거 포함)
def load_words_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
        words = text.upper().split()  # 대소문자 통일
        cleaned_words = {word.strip(".,!?/\\()[]{}<>\"'") for word in words}  # set으로 변환하여 중복 제거
        return cleaned_words

# 기준 단어와 비교하는 함수
def compare_words(file_words, reference_words):
    reference_set = set(reference_words)
    matched = reference_set.intersection(file_words)
    return matched, len(matched)

# 사용 예시
if __name__ == '__main__':
    file_path = './RedSWUS-flask/finalResult/final_str_result.txt'  # 파일 경로 수정 가능
    file_words = load_words_from_file(file_path)
    total_words = len(file_words)
    matched_words, matched_count = compare_words(file_words, reference_words)

    print(f"총 {total_words}개의 고유 단어 중에서 {matched_count}개의 단어가 기준 단어와 일치합니다.")
    print("일치한 단어 목록:")
    for word in sorted(matched_words):
        print(word)
