GROUPS = {
    'A': ['Mexico', 'South Africa', 'South Korea', 'Czech Republic'],
    'B': ['Canada', 'Switzerland', 'Qatar', 'Bosnia and Herzegovina'],
    'C': ['Brazil', 'Morocco', 'Scotland', 'Haiti'],
    'D': ['USA', 'Paraguay', 'Australia', 'Turkey'],
    'E': ['Germany', 'Curaçao', 'Ivory Coast', 'Ecuador'],
    'F': ['Netherlands', 'Japan', 'Tunisia', 'Sweden'],
    'G': ['Belgium', 'Egypt', 'Iran', 'New Zealand'],
    'H': ['Spain', 'Cape Verde', 'Saudi Arabia', 'Uruguay'],
    'I': ['France', 'Senegal', 'Norway', 'Iraq'],
    'J': ['Argentina', 'Algeria', 'Austria', 'Jordan'],
    'K': ['Portugal', 'Colombia', 'Uzbekistan', 'DR Congo'],
    'L': ['England', 'Croatia', 'Ghana', 'Panama'],
}

ALL_TEAMS = sorted([t for teams in GROUPS.values() for t in teams])

# Flag emojis for teams
FLAGS = {
    'Mexico': '🇲🇽', 'South Africa': '🇿🇦', 'South Korea': '🇰🇷',
    'Czech Republic': '🇨🇿', 'Canada': '🇨🇦', 'Switzerland': '🇨🇭',
    'Qatar': '🇶🇦', 'Bosnia and Herzegovina': '🇧🇦', 'Brazil': '🇧🇷',
    'Morocco': '🇲🇦', 'Scotland': ' ⚽', 'Haiti': '🇭🇹',
    'USA': '🇺🇸', 'Paraguay': '🇵🇾', 'Australia': '🇦🇺',
    'Turkey': '🇹🇷', 'Germany': '🇩🇪', 'Curaçao': '🇨🇼',
    'Ivory Coast': '🇨🇮', 'Ecuador': '🇪🇨', 'Netherlands': '🇳🇱',
    'Japan': '🇯🇵', 'Tunisia': '🇹🇳', 'Sweden': '🇸🇪',
    'Belgium': '🇧🇪', 'Egypt': '🇪🇬', 'Iran': '🇮🇷',
    'New Zealand': '🇳🇿', 'Spain': '🇪🇸', 'Cape Verde': '🇨🇻',
    'Saudi Arabia': '🇸🇦', 'Uruguay': '🇺🇾', 'France': '🇫🇷',
    'Senegal': '🇸🇳', 'Norway': '🇳🇴', 'Iraq': '🇮🇶',
    'Argentina': '🇦🇷', 'Algeria': '🇩🇿', 'Austria': '🇦🇹',
    'Jordan': '🇯🇴', 'Portugal': '🇵🇹', 'Colombia': '🇨🇴',
    'Uzbekistan': '🇺🇿', 'DR Congo': '🇨🇩', 'England': ' ⚽',
    'Croatia': '🇭🇷', 'Ghana': '🇬🇭', 'Panama': '🇵🇦',
}

def get_flag(team):
    return FLAGS.get(team, '🏳️')
