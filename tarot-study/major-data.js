// 메이저 22장: 원본 PNG와 눈 영역 좌표는 각각 보관한다.
window.TAROT_SAMPLES = [
  {
    "id": "major-00",
    "numeral": "0",
    "title": "THE FOOL",
    "korean": "바보",
    "tone": "GOLDEN DAWN",
    "atlas": "art/fool-redrawn-atlas.png",
    "description": "흰 장미와 작은 친구, 그리고 첫걸음.",
    "effect": "sun-halo",
    "category": "MAJOR ARCANA"
  },
  {
    "id": "major-01",
    "numeral": "I",
    "title": "THE MAGICIAN",
    "korean": "마법사",
    "tone": "LEMON MAGIC",
    "atlas": "art/magician-atlas.png",
    "description": "위로 든 지팡이와 네 수트의 상징.",
    "effect": "magic-light",
    "category": "MAJOR ARCANA"
  },
  {
    "id": "major-02",
    "numeral": "II",
    "title": "THE HIGH PRIESTESS",
    "korean": "여사제",
    "tone": "MIDNIGHT VEIL",
    "description": "검고 흰 기둥, 석류 장막과 초승달. 고요한 달빛 속 여사제.",
    "effect": "moon",
    "atlas": "art/major-02-atlas-v2.png",
    "category": "MAJOR ARCANA"
  },
  {
    "id": "major-03",
    "numeral": "III",
    "title": "THE EMPRESS",
    "korean": "여황제",
    "tone": "GOLDEN HARVEST",
    "description": "별 왕관과 밀밭, 금빛 홀을 든 여황제.",
    "effect": "petal",
    "atlas": "art/major-03-atlas.png",
    "category": "MAJOR ARCANA"
  },
  {
    "id": "major-04",
    "numeral": "IV",
    "title": "THE EMPEROR",
    "korean": "황제",
    "tone": "STONE & GOLD",
    "description": "양 머리 왕좌, 홀과 보주가 만드는 단단한 중심.",
    "effect": "glow",
    "atlas": "art/major-04-atlas.png",
    "category": "MAJOR ARCANA"
  },
  {
    "id": "major-05",
    "numeral": "V",
    "title": "THE HIEROPHANT",
    "korean": "교황",
    "tone": "IVORY RITUAL",
    "description": "세 겹 왕관과 교차한 열쇠, 두 제자를 맞는 교황.",
    "effect": "glow",
    "atlas": "art/major-05-atlas.png",
    "category": "MAJOR ARCANA"
  },
  {
    "id": "major-06",
    "numeral": "VI",
    "title": "THE LOVERS",
    "korean": "연인",
    "tone": "TENDER DAWN",
    "description": "두 사람과 축복의 천사, 선택과 조화를 담은 연인.",
    "effect": "petal",
    "atlas": "art/major-06-atlas.png",
    "category": "MAJOR ARCANA"
  },
  {
    "id": "major-07",
    "numeral": "VII",
    "title": "THE CHARIOT",
    "korean": "전차",
    "tone": "STAR CANOPY",
    "description": "별 천막 아래 전차와 검고 흰 스핑크스.",
    "effect": "glow",
    "atlas": "art/major-07-atlas.png",
    "category": "MAJOR ARCANA"
  },
  {
    "id": "major-08",
    "numeral": "VIII",
    "title": "STRENGTH",
    "korean": "힘",
    "tone": "GENTLE COURAGE",
    "description": "사자를 다정히 어루만지는 레몬과 무한대의 상징.",
    "effect": "petal",
    "atlas": "art/major-08-atlas.png",
    "category": "MAJOR ARCANA"
  },
  {
    "id": "major-09",
    "numeral": "IX",
    "title": "THE HERMIT",
    "korean": "은둔자",
    "tone": "LANTERN IN SNOW",
    "description": "설산 위의 등불, 별빛을 품은 은둔자.",
    "effect": "lantern",
    "atlas": "art/major-09-atlas-v3.png",
    "category": "MAJOR ARCANA"
  },
  {
    "id": "major-10",
    "numeral": "X",
    "title": "WHEEL OF FORTUNE",
    "korean": "운명의 수레바퀴",
    "tone": "TURNING HEAVENS",
    "description": "수레바퀴와 네 모서리의 수호자, 변화의 흐름.",
    "effect": "wheel",
    "atlas": "art/major-10-atlas-v3.png",
    "foreground_clip": "inset(0 0 0 50.41436464%)",
    "overlays": [
      {
        "file": "art/major-10-corner-symbols-v2.png",
        "clip": "inset(0 50% 0 0)",
        "scale": 0.7,
        "origin": "0% 100%",
        "description": "책을 든 날개 달린 황소"
      },
      {
        "file": "art/major-10-corner-symbols-v2.png",
        "clip": "inset(0 0 0 50%)",
        "scale": 0.7,
        "origin": "100% 100%",
        "description": "책을 든 날개 달린 사자"
      }
    ],
    "category": "MAJOR ARCANA"
  },
  {
    "id": "major-11",
    "numeral": "XI",
    "title": "JUSTICE",
    "korean": "정의",
    "tone": "BALANCED LIGHT",
    "description": "곧게 든 검과 수평의 저울, 공정한 판단.",
    "effect": "glow",
    "atlas": "art/major-11-atlas.png",
    "category": "MAJOR ARCANA"
  },
  {
    "id": "major-12",
    "numeral": "XII",
    "title": "THE HANGED MAN",
    "korean": "매달린 사람",
    "tone": "QUIET PERSPECTIVE",
    "description": "한쪽 발로 매달린 레몬, 시선을 바꾸는 고요한 순간.",
    "effect": "halo",
    "atlas": "art/major-12-atlas-v2.png",
    "foreground_clip": "inset(0 0 0 51.24395301%)",
    "category": "MAJOR ARCANA"
  },
  {
    "id": "major-13",
    "numeral": "XIII",
    "title": "DEATH",
    "korean": "죽음",
    "tone": "A NEW DAWN",
    "description": "왕의 종결과 서로 다른 응답, 두 탑 사이로 떠오르는 해.",
    "effect": "petal",
    "atlas": "art/major-13-atlas-v2.png",
    "foreground_clip": "inset(0 0 0 50.20718232%)",
    "foreground_scale": 0.68,
    "foreground_origin": "0% 96%",
    "foreground_offset_y": -15,
    "category": "MAJOR ARCANA"
  },
  {
    "id": "major-14",
    "numeral": "XIV",
    "title": "TEMPERANCE",
    "korean": "절제",
    "tone": "FLOWING HARMONY",
    "description": "두 잔 사이로 흐르는 물, 물가와 땅의 균형.",
    "effect": "water",
    "atlas": "art/major-14-atlas-v3.png",
    "fixed_foreground": {
      "split": 82,
      "role": "물가·육지의 발 접점 고정"
    },
    "category": "MAJOR ARCANA"
  },
  {
    "id": "major-15",
    "numeral": "XV",
    "title": "THE DEVIL",
    "korean": "악마",
    "tone": "VELVET SHADOW",
    "description": "뿔과 날개, 느슨한 사슬로 표현한 악마의 상징.",
    "effect": "ember",
    "atlas": "art/major-15-atlas.png",
    "category": "MAJOR ARCANA"
  },
  {
    "id": "major-16",
    "numeral": "XVI",
    "title": "THE TOWER",
    "korean": "탑",
    "tone": "A SUDDEN SPARK",
    "description": "번개와 흔들린 왕관, 갑작스러운 변화를 담은 탑.",
    "effect": "lightning",
    "atlas": "art/major-16-atlas-v4.png",
    "foreground_clip": "inset(0 0 0 50.27662517%)",
    "foreground_scale": 0.66,
    "foreground_origin": "90% 94%",
    "category": "MAJOR ARCANA"
  },
  {
    "id": "major-17",
    "numeral": "XVII",
    "title": "THE STAR",
    "korean": "별",
    "tone": "HOPE BY WATER",
    "description": "큰 별과 일곱 작은 별, 두 물병에 담은 희망.",
    "effect": "water",
    "atlas": "art/major-17-atlas-v4.png",
    "fixed_foreground": {
      "split": 88,
      "role": "무릎·얕은 물·붓는 물의 착지점 고정"
    },
    "category": "MAJOR ARCANA"
  },
  {
    "id": "major-18",
    "numeral": "XVIII",
    "title": "THE MOON",
    "korean": "달",
    "tone": "DREAMING PATH",
    "description": "달과 두 탑, 개와 늑대가 지키는 밤의 길.",
    "effect": "moon",
    "atlas": "art/major-18-atlas-v4.png",
    "foreground_clip": "inset(0 0 0 50.69060773%)",
    "foreground_scale": 0.82,
    "foreground_origin": "85% 94%",
    "scene_file": "art/major-18-path-scenery-v2.png",
    "category": "MAJOR ARCANA"
  },
  {
    "id": "major-19",
    "numeral": "XIX",
    "title": "THE SUN",
    "korean": "태양",
    "tone": "LEMON SUMMER",
    "description": "햇살과 해바라기, 흰 말을 타고 든 붉은 깃발.",
    "effect": "sun",
    "atlas": "art/major-19-atlas.png",
    "foreground_clip": "inset(0 0 0 50.27624309%)",
    "foreground_scale": 0.9,
    "foreground_origin": "50% 96%",
    "category": "MAJOR ARCANA"
  },
  {
    "id": "major-20",
    "numeral": "XX",
    "title": "JUDGEMENT",
    "korean": "심판",
    "tone": "THE AWAKENING",
    "description": "나팔과 붉은 십자 깃발, 깨어나는 사람들.",
    "effect": "glow",
    "atlas": "art/major-20-atlas.png",
    "foreground_clip": "inset(0 0 0 50.20718232%)",
    "fixed_foreground": {
      "split": 86,
      "role": "인물이 일어나는 석관은 전경 하단에만 고정"
    },
    "scene_atlas": "art/major-20-atlas-v2.png",
    "category": "MAJOR ARCANA"
  },
  {
    "id": "major-21",
    "numeral": "XXI",
    "title": "THE WORLD",
    "korean": "세계",
    "tone": "A COMPLETE CIRCLE",
    "description": "월계수 고리와 두 지팡이, 여행의 완성과 새로운 시작.",
    "effect": "petal",
    "atlas": "art/major-21-atlas.png",
    "category": "MAJOR ARCANA"
  }
];
window.TAROT_BLINKS = {
  "major-00": {
    "file": "art/fool-blink.png",
    "eyes": [
      [
        264,
        290,
        38,
        43
      ],
      [
        350,
        311,
        40,
        43
      ]
    ]
  },
  "major-01": {
    "file": "art/magician-blink.png",
    "eyes": [
      [
        283,
        334,
        38,
        44
      ],
      [
        374,
        351,
        40,
        44
      ]
    ]
  },
  "major-02": {
    "file": "art/major-02-blink-v2.png",
    "eyes": [
      [
        304,
        344,
        38,
        43
      ],
      [
        386,
        348,
        38,
        43
      ]
    ],
    "panel": [
      723.5,
      1087
    ]
  },
  "major-03": {
    "file": "art/major-03-blink.png",
    "eyes": [
      [
        299,
        328,
        38,
        43
      ],
      [
        381,
        349,
        38,
        43
      ]
    ],
    "panel": [
      724.0,
      1086
    ]
  },
  "major-04": {
    "file": "art/major-04-blink.png",
    "eyes": [
      [
        295,
        352,
        38,
        43
      ],
      [
        380,
        361,
        38,
        43
      ]
    ],
    "panel": [
      724.0,
      1086
    ]
  },
  "major-05": {
    "file": "art/major-05-blink.png",
    "eyes": [
      [
        308,
        332,
        34,
        39
      ],
      [
        383,
        342,
        34,
        39
      ]
    ],
    "panel": [
      724.0,
      1086
    ]
  },
  "major-06": {
    "file": "art/major-06-blink.png",
    "eyes": [
      [
        183,
        582,
        29,
        35
      ],
      [
        245,
        568,
        29,
        35
      ],
      [
        496,
        550,
        28,
        34
      ],
      [
        554,
        555,
        28,
        34
      ]
    ],
    "panel": [
      724.0,
      1086
    ]
  },
  "major-07": {
    "file": "art/major-07-blink.png",
    "eyes": [
      [
        312,
        346,
        37,
        43
      ],
      [
        389,
        355,
        37,
        43
      ]
    ],
    "panel": [
      724.0,
      1086
    ]
  },
  "major-08": {
    "file": "art/major-08-blink.png",
    "eyes": [
      [
        318,
        367,
        38,
        45
      ],
      [
        405,
        395,
        38,
        45
      ]
    ],
    "panel": [
      724.0,
      1086
    ]
  },
  "major-09": {
    "file": "art/major-09-blink-v2.png",
    "eyes": [
      [
        292,
        328,
        38,
        43
      ],
      [
        374,
        350,
        38,
        43
      ]
    ],
    "panel": [
      723.5,
      1087
    ]
  },
  "major-10": {
    "file": "art/major-10-blink.png",
    "eyes": [
      [
        326,
        243,
        31,
        37
      ],
      [
        395,
        258,
        31,
        37
      ]
    ],
    "panel": [
      724.0,
      1086
    ]
  },
  "major-11": {
    "file": "art/major-11-blink.png",
    "eyes": [
      [
        297,
        367,
        38,
        45
      ],
      [
        379,
        375,
        38,
        45
      ]
    ],
    "panel": [
      724.0,
      1086
    ]
  },
  "major-12": {
    "file": "art/major-12-blink-v2.png",
    "eyes": [
      [
        316,
        703,
        33,
        39
      ],
      [
        386,
        713,
        33,
        39
      ]
    ],
    "panel": [
      723.5,
      1087
    ]
  },
  "major-13": {
    "file": "art/major-13-blink-v2.png",
    "eyes": [
      [
        285,
        425,
        23,
        27
      ],
      [
        329,
        438,
        16,
        24
      ]
    ],
    "panel": [
      724.0,
      1086
    ]
  },
  "major-14": {
    "file": "art/major-14-blink-v2.png",
    "eyes": [
      [
        349,
        323,
        38,
        43
      ],
      [
        431,
        348,
        38,
        43
      ]
    ],
    "panel": [
      723.5,
      1087
    ]
  },
  "major-15": {
    "file": "art/major-15-blink.png",
    "eyes": [
      [
        304,
        314,
        37,
        42
      ],
      [
        381,
        331,
        37,
        42
      ]
    ],
    "panel": [
      724.0,
      1086
    ]
  },
  "major-16": {
    "file": "art/major-16-blink-v2.png",
    "eyes": [
      [
        500,
        551,
        28,
        33
      ],
      [
        552,
        585,
        28,
        33
      ]
    ],
    "panel": [
      723.0,
      1088
    ]
  },
  "major-17": {
    "file": "art/major-17-blink-v2.png",
    "eyes": [
      [
        326,
        531,
        31,
        35
      ],
      [
        400,
        556,
        31,
        35
      ]
    ],
    "panel": [
      723.0,
      1087
    ]
  },
  "major-18": {
    "file": "art/major-18-blink-v2.png",
    "eyes": [
      [
        304,
        402,
        34,
        41
      ],
      [
        376,
        424,
        34,
        41
      ]
    ],
    "panel": [
      724.0,
      1086
    ]
  },
  "major-19": {
    "file": "art/major-19-blink.png",
    "eyes": [
      [
        300,
        337,
        34,
        41
      ],
      [
        374,
        353,
        34,
        41
      ]
    ],
    "panel": [
      724.0,
      1086
    ]
  },
  "major-20": {
    "file": "art/major-20-blink.png",
    "eyes": [
      [
        315,
        276,
        31,
        37
      ],
      [
        382,
        291,
        31,
        37
      ]
    ],
    "panel": [
      724.0,
      1086
    ]
  },
  "major-21": {
    "file": "art/major-21-blink.png",
    "eyes": [
      [
        299,
        344,
        38,
        45
      ],
      [
        381,
        369,
        38,
        45
      ]
    ],
    "panel": [
      724.0,
      1086
    ]
  }
};
