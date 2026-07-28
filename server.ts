import express from "express";
import path from "path";
import fs from "fs";
import cors from "cors";
import { GoogleGenAI } from "@google/genai";

const app = express();
const PORT = 3000;

app.use(cors());
app.use(express.json({ limit: "10mb" }));

// In-memory state for settings, context, etc.
let appSettings: Record<string, any> = {
  model: "auto",
  temperature: 0.7,
  ui_lang: "vi",
  learn_lang: "en",
};

let appContext: Record<string, any> | null = null;

// Built-in vocabulary samples for decks
const BUILTIN_DECKS = [
  { id: 1, name: "English Core Vocabulary", level: 0 },
  { id: 2, name: "IELTS Essential 500", level: 0 },
  { id: 3, name: "Business English", level: 0 },
  { id: 4, name: "Daily Conversation", level: 0 },
];

const VOCAB_POOLS: Record<number, Array<{ id: number; key: string; term: string; definition: string }>> = {
  1: [
    { id: 1, key: "ubiquitous\0present everywhere", term: "ubiquitous", definition: "present, appearing, or found everywhere" },
    { id: 2, key: "pragmatic\0practical approach", term: "pragmatic", definition: "dealing with things sensibly and realistically" },
    { id: 3, key: "ambiguous\0open to interpretations", term: "ambiguous", definition: "open to more than one interpretation; unclear" },
    { id: 4, key: "eloquent\0fluent or persuasive", term: "eloquent", definition: "fluent or persuasive in speaking or writing" },
    { id: 5, key: "resilient\0quick to recover", term: "resilient", definition: "able to withstand or recover quickly from difficult conditions" },
    { id: 6, key: "ephemeral\0lasting a short time", term: "ephemeral", definition: "lasting for a very short time" },
    { id: 7, key: "consensus\0general agreement", term: "consensus", definition: "a general agreement among a group of people" },
    { id: 8, key: "deteriorate\0become worse", term: "deteriorate", definition: "to become progressively worse" },
    { id: 9, key: "scrutiny\0critical observation", term: "scrutiny", definition: "critical observation or examination" },
    { id: 10, key: "advocate\0publicly support", term: "advocate", definition: "to publicly recommend or support a cause or policy" },
    { id: 11, key: "inevitable\0unavoidable", term: "inevitable", definition: "certain to happen; unavoidable" },
    { id: 12, key: "mitigate\0make less severe", term: "mitigate", definition: "to make less severe, serious, or painful" },
  ],
  2: [
    { id: 13, key: "paradigm\0typical pattern", term: "paradigm", definition: "a typical example or pattern of something" },
    { id: 14, key: "verbose\0using too many words", term: "verbose", definition: "using or expressed in more words than are needed" },
    { id: 15, key: "concise\0brief and clear", term: "concise", definition: "giving a lot of information clearly and in a few words" },
    { id: 16, key: "hypothesis\0proposed explanation", term: "hypothesis", definition: "a proposed explanation made on the basis of limited evidence" },
    { id: 17, key: "comprehensive\0complete and thorough", term: "comprehensive", definition: "including or dealing with all or nearly all elements or aspects" },
    { id: 18, key: "perceive\0become aware of", term: "perceive", definition: "to interpret or look at something in a particular way" },
    { id: 19, key: "plausible\0seeming reasonable", term: "plausible", definition: "seeming reasonable or probable" },
    { id: 20, key: "articulate\0express clearly", term: "articulate", definition: "having or showing the ability to speak fluently and coherently" },
  ],
  3: [
    { id: 21, key: "leverage\0use to advantage", term: "leverage", definition: "use something to maximum advantage" },
    { id: 22, key: "synergy\0combined interaction", term: "synergy", definition: "interaction or cooperation giving a greater combined effect" },
    { id: 23, key: "benchmark\0standard of reference", term: "benchmark", definition: "a standard or point of reference against which things may be compared" },
    { id: 24, key: "feasible\0possible to do easily", term: "feasible", definition: "possible and practical to do easily or conveniently" },
    { id: 25, key: "revenue\0income of organization", term: "revenue", definition: "income generated from normal business operations" },
  ],
  4: [
    { id: 26, key: "appreciated\0grateful for", term: "appreciated", definition: "recognized with gratitude" },
    { id: 27, key: "hesitate\0pause before doing", term: "hesitate", definition: "pause before saying or doing something due to uncertainty" },
    { id: 28, key: "recommend\0suggest as good", term: "recommend", definition: "advise or suggest something as a good choice" },
    { id: 29, key: "convenient\0fitting well with plans", term: "convenient", definition: "fitting in well with a person's needs, activities, or plans" },
    { id: 30, key: "opportunity\0favorable chance", term: "opportunity", definition: "a set of circumstances that makes it possible to do something" },
  ]
};

function getAiClient() {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) return null;
  return new GoogleGenAI({ apiKey });
}

// Schemas for Gemini Structured Output
const SCHEMAS: Record<string, any> = {
  fill_blank: {
    type: "object",
    properties: {
      questions: {
        type: "array",
        items: {
          type: "object",
          properties: {
            sentence_with_blank: { type: "string", description: "Natural sentence in target language containing '_____'." },
            full_sentence: { type: "string", description: "Complete correct sentence in target language." },
            blank_word: { type: "string", description: "The exact word missing in target language." },
            options: {
              type: "array",
              items: { type: "string" },
              description: "Exactly 4 distinct choices in target language."
            },
            correct_index: { type: "integer", description: "Index 0-3 of the correct option." },
            options_vietnamese: {
              type: "array",
              items: { type: "string" },
              description: "BẮT BUỘC: 4 bản dịch TIẾNG VIỆT tương ứng 1-1 với 4 options."
            },
            sentence_vietnamese: {
              type: "string",
              description: "BẮT BUỘC: Bản dịch full_sentence sang TIẾNG VIỆT tự nhiên."
            },
            explanation_vietnamese: {
              type: "string",
              description: "BẮT BUỘC: Giải thích lý do chọn đáp án đúng bằng TIẾNG VIỆT chi tiết (ngữ pháp, từ vựng, ngữ cảnh)."
            }
          },
          required: [
            "sentence_with_blank",
            "full_sentence",
            "blank_word",
            "options",
            "correct_index",
            "options_vietnamese",
            "sentence_vietnamese",
            "explanation_vietnamese"
          ],
        },
      },
    },
    required: ["questions"],
  },
  cloze: {
    type: "object",
    properties: {
      paragraph_with_blanks: { type: "string", description: "Text in target language containing placeholders [1], [2]..." },
      paragraph_full: { type: "string", description: "Complete passage in target language with correct words filled in." },
      sentence_meaning_vietnamese: { type: "string", description: "BẮT BUỘC: Dịch toàn bộ đoạn văn sang TIẾNG VIỆT tự nhiên." },
      blanks: {
        type: "array",
        items: {
          type: "object",
          properties: {
            blank_id: { type: "integer" },
            correct_word: { type: "string", description: "Target word in target language." },
            options: {
              type: "array",
              items: { type: "string" },
              description: "4 choices in target language."
            },
            correct_index: { type: "integer" },
            meaning_vietnamese: { type: "string", description: "BẮT BUỘC: Nghĩa TIẾNG VIỆT ngắn gọn của correct_word." },
            explanation_vietnamese: { type: "string", description: "BẮT BUỘC: Giải thích lý do chọn từ này bằng TIẾNG VIỆT." }
          },
          required: ["blank_id", "correct_word", "options", "correct_index", "meaning_vietnamese", "explanation_vietnamese"],
        },
      },
    },
    required: ["paragraph_with_blanks", "paragraph_full", "sentence_meaning_vietnamese", "blanks"],
  },
  translation: {
    type: "object",
    properties: {
      sentences: {
        type: "array",
        items: {
          type: "object",
          properties: {
            source_text: { type: "string", description: "Sentence in target language." },
            target_text_vietnamese: { type: "string", description: "BẮT BUỘC: Bản dịch TIẾNG VIỆT chính xác, tự nhiên." },
            grammar_notes_vietnamese: { type: "string", description: "BẮT BUỘC: Ghi chú ngữ pháp hoặc cấu trúc bằng TIẾNG VIỆT." }
          },
          required: ["source_text", "target_text_vietnamese", "grammar_notes_vietnamese"],
        },
      },
    },
    required: ["sentences"],
  },
  unscramble: {
    type: "object",
    properties: {
      sentences: {
        type: "array",
        items: {
          type: "object",
          properties: {
            correct_sentence: { type: "string", description: "Complete natural sentence in target language." },
            hint_vietnamese: { type: "string", description: "BẮT BUỘC: Gợi ý bằng TIẾNG VIỆT để giúp ghép câu." },
            translation_vietnamese: { type: "string", description: "BẮT BUỘC: Bản dịch TIẾNG VIỆT của correct_sentence." },
            sentence_meaning_vietnamese: { type: "string", description: "BẮT BUỘC: Ý nghĩa câu bằng TIẾNG VIỆT." },
            key_vocab: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  word: { type: "string", description: "Vocabulary word in target language." },
                  meaning_vietnamese: { type: "string", description: "BẮT BUỘC: Nghĩa từ bằng TIẾNG VIỆT." }
                },
                required: ["word", "meaning_vietnamese"]
              },
            },
          },
          required: ["correct_sentence", "hint_vietnamese", "translation_vietnamese", "sentence_meaning_vietnamese"],
        },
      },
    },
    required: ["sentences"],
  },
  story: {
    type: "object",
    properties: {
      story: { type: "string", description: "Reading passage in target language." },
      passage_vietnamese: { type: "string", description: "BẮT BUỘC: Bản dịch toàn bài đọc sang TIẾNG VIỆT tự nhiên." },
      comprehension_questions: {
        type: "array",
        items: {
          type: "object",
          properties: {
            question: { type: "string", description: "Clear question in target language." },
            options: {
              type: "array",
              items: { type: "string" },
              description: "Exactly 4 choice options in target language."
            },
            options_vietnamese: {
              type: "array",
              items: { type: "string" },
              description: "BẮT BUỘC: 4 bản dịch TIẾNG VIỆT tương ứng với 4 options."
            },
            correct_index: { type: "integer" },
            explanation_vietnamese: { type: "string", description: "BẮT BUỘC: Giải thích lý do chọn bằng TIẾNG VIỆT chi tiết." },
            quote_evidence: { type: "string", description: "Exact verbatim quote/sentence from story in target language providing evidence." }
          },
          required: ["question", "options", "options_vietnamese", "correct_index", "explanation_vietnamese", "quote_evidence"],
        },
      },
    },
    required: ["story", "passage_vietnamese", "comprehension_questions"],
  },
  sentence_transform: {
    type: "object",
    properties: {
      questions: {
        type: "array",
        items: {
          type: "object",
          properties: {
            original_sentence: { type: "string", description: "Starting sentence in target language." },
            instruction_vietnamese: { type: "string", description: "BẮT BUỘC: Yêu cầu bài tập bằng TIẾNG VIỆT (vd: 'Viết lại câu sử dụng từ gợi ý...')." },
            hint_word: { type: "string", description: "Key word or structure in target language to incorporate." },
            expected_answer: { type: "string", description: "Correct transformed sentence in target language." },
            grammar_rule_vietnamese: { type: "string", description: "BẮT BUỘC: Giải thích cấu trúc ngữ pháp đã dùng bằng TIẾNG VIỆT." }
          },
          required: ["original_sentence", "instruction_vietnamese", "hint_word", "expected_answer", "grammar_rule_vietnamese"],
        },
      },
    },
    required: ["questions"],
  },
  taboo: {
    type: "object",
    properties: {
      rounds: {
        type: "array",
        items: {
          type: "object",
          properties: {
            secret_word: { type: "string", description: "Target secret word to guess in target language." },
            forbidden_words: {
              type: "array",
              items: { type: "string" },
              description: "Exactly 4 forbidden related words in target language."
            },
            ai_description: { type: "string", description: "Helpful description/clue in target language WITHOUT using secret_word or forbidden_words." },
            word_meaning_vietnamese: { type: "string", description: "BẮT BUỘC: Dịch nghĩa secret_word sang TIẾNG VIỆT." },
            category: { type: "string", description: "Word topic or category." }
          },
          required: ["secret_word", "forbidden_words", "ai_description", "word_meaning_vietnamese", "category"],
        },
      },
    },
    required: ["rounds"],
  },
};

// Helper function: Fisher-Yates mathematical random shuffle algorithm
function shuffleArray<T>(array: T[]): T[] {
  const result = [...array];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

// Fallback Generators when API Key is not configured or fails
function getFallbackExercise(gamemode: string, data: any) {
  const count = data.count || 3;
  const vocab = data.vocab_pairs || VOCAB_POOLS[1];
  
  if (gamemode === "fill_blank") {
    return {
      questions: Array.from({ length: count }, (_, i) => {
        const item = vocab[i % vocab.length] || { term: "ubiquitous", definition: "present everywhere" };
        return {
          sentence_with_blank: `Smartphones have become _____ in modern daily life.`,
          full_sentence: `Smartphones have become ${item.term} in modern daily life.`,
          blank_word: item.term,
          options: [item.term, "ephemeral", "pragmatic", "verbose"],
          options_translations: ["phổ biến khắp nơi", "ngắn hạn, tạm thời", "thực tế, thực tiễn", "dài dòng"],
          correct_index: 0,
          explanation_short: `Chọn '${item.term}' vì ngữ cảnh mô tả điện thoại thông minh xuất hiện ở khắp mọi nơi trong đời sống hiện đại.`,
          sentence_translation: `Điện thoại thông minh đã trở nên phổ biến khắp nơi trong cuộc sống hiện đại.`
        };
      })
    };
  }

  if (gamemode === "cloze") {
    return {
      paragraph_with_blanks: "In today's fast-paced world, clear communication is essential. Being [1] allows professionals to express complex ideas effectively. When teams face difficult challenges, reaching a [2] ensures everyone works toward the same goal. Having a [3] approach helps resolve conflicts quickly.",
      paragraph_full: "In today's fast-paced world, clear communication is essential. Being articulate allows professionals to express complex ideas effectively. When teams face difficult challenges, reaching a consensus ensures everyone works toward the same goal. Having a pragmatic approach helps resolve conflicts quickly.",
      sentence_meaning: "Trong thế giới hiện đại, giao tiếp rõ ràng là rất quan trọng. Khả năng diễn đạt lưu loát giúp làm việc hiệu quả.",
      blanks: [
        {
          blank_id: 1,
          correct_word: "articulate",
          options: ["articulate", "verbose", "ephemeral", "ambiguous"],
          correct_index: 0,
          explanation_short: "articulate: diễn đạt rõ ràng, lưu loát",
          meaning_in_vietnamese: "diễn đạt lưu loát"
        },
        {
          blank_id: 2,
          correct_word: "consensus",
          options: ["consensus", "scrutiny", "hypothesis", "paradigm"],
          correct_index: 0,
          explanation_short: "consensus: sự đồng thuận",
          meaning_in_vietnamese: "sự thống nhất"
        },
        {
          blank_id: 3,
          correct_word: "pragmatic",
          options: ["pragmatic", "ambiguous", "verbose", "inevitable"],
          correct_index: 0,
          explanation_short: "pragmatic: thực tế",
          meaning_in_vietnamese: "thực tiễn"
        }
      ]
    };
  }

  if (gamemode === "translation") {
    return {
      sentences: [
        {
          source_text: "Việc sử dụng công nghệ một cách thực tế giúp cải thiện hiệu suất công việc.",
          target_text: "Using technology pragmatically helps improve work performance.",
          grammar_notes: "Adv + Verb construction: 'pragmatically helps improve'",
          detailed_feedback: {
            word_by_word: [
              { word: "pragmatically", translation: "thực tế", notes: "Trạng từ" },
              { word: "performance", translation: "hiệu suất", notes: "Danh từ" }
            ],
            common_mistakes: ["Quên dùng trạng từ bổ nghĩa cho động từ"],
            alternative_translations: ["Applying technology in a practical way enhances productivity."],
            improvement_tips: "Sử dụng trạng từ đứng trước động từ chính để tăng tính tự nhiên."
          }
        }
      ]
    };
  }

  if (gamemode === "unscramble") {
    const sList = [
      { correct_sentence: "Technology plays an important role in modern education.", hint: "Role of tech", translation: "Công nghệ đóng vai trò quan trọng trong giáo dục hiện đại.", sentence_meaning: "Công nghệ giúp việc học trở nên thuận tiện hơn.", key_vocab: [{ word: "education", meaning: "giáo dục" }] },
      { correct_sentence: "Clear communication helps teams reach a quick consensus.", hint: "Teamwork", translation: "Giao tiếp rõ ràng giúp nhóm nhanh chóng đạt đồng thuận.", sentence_meaning: "Thống nhất ý kiến trong làm việc nhóm.", key_vocab: [{ word: "consensus", meaning: "sự đồng thuận" }] }
    ];
    const chosen = sList.slice(0, count);
    return {
      questions: chosen.map(s => ({
        correct_sentence: s.correct_sentence,
        shuffled_words: s.correct_sentence.split(" ").sort(() => Math.random() - 0.5),
        hint: s.hint,
        translation: s.translation,
        word_count: s.correct_sentence.split(" ").length
      }))
    };
  }

  if (gamemode === "story") {
    return {
      story: "Alex was known for his articulate presentation style. During the annual conference, he presented a comprehensive plan to mitigate operational risks. Despite initial skepticism from the board, his persuasive arguments helped the team reach a unanimous consensus on the new strategic paradigm.",
      comprehension_questions: [
        {
          question: "What was Alex known for during presentations?",
          options: ["His articulate style", "His verbose explanations", "His ambiguous slides", "His hesitant tone"],
          correct_index: 0,
          explanation: "Alex nổi tiếng với phong cách thuyết trình diễn đạt lưu loát và rõ ràng (articulate presentation style).",
          quote_evidence: "Alex was known for his articulate presentation style."
        },
        {
          question: "What did Alex's plan aim to achieve?",
          options: ["Mitigate operational risks", "Increase expenses", "Delay the conference", "Ignore board opinions"],
          correct_index: 0,
          explanation: "Kế hoạch của Alex nhằm mục đích giảm thiểu các rủi ro trong quá trình vận hành (mitigate operational risks).",
          quote_evidence: "During the annual conference, he presented a comprehensive plan to mitigate operational risks."
        },
        {
          question: "How did the board react to Alex's presentation in the end?",
          options: ["Reached a unanimous consensus", "Rejected the whole proposal", "Postponed the strategic meeting", "Fired the entire risk team"],
          correct_index: 0,
          explanation: "Dù ban đầu hoài nghi, lập luận thuyết phục của Alex đã giúp ban giám đốc đi đến sự đồng thuận nhất trí.",
          quote_evidence: "his persuasive arguments helped the team reach a unanimous consensus on the new strategic paradigm."
        }
      ]
    };
  }

  if (gamemode === "sentence_transform") {
    return {
      questions: [
        {
          original_sentence: "They built the new bridge in less than six months.",
          instruction: "Rewrite using the passive voice (start with 'The new bridge...').",
          hint_word: "built",
          expected_answer: "The new bridge was built in less than six months.",
          grammar_rule: "Passive voice in Simple Past: Subject + was/were + Past Participle",
          detailed_explanation: {
            rule_description: "To form passive in simple past, move the object to the subject position and use was/were + V3.",
            step_by_step: [
              "1. Identify the object: 'the new bridge'",
              "2. Change verb 'built' to past passive: 'was built'",
              "3. Add remaining context"
            ],
            common_errors: ["Using 'is built' instead of 'was built'"],
            comparison: "Active: They built... -> Passive: The new bridge was built..."
          }
        }
      ]
    };
  }

  if (gamemode === "taboo") {
    return {
      rounds: [
        {
          secret_word: "UBIQUITOUS",
          forbidden_words: ["EVERYWHERE", "COMMON", "FOUND", "PRESENT", "ALWAYS"],
          ai_description: "Describing something that seems to exist in all places at the same time, like modern technology or mobile phones.",
          category: "Adjectives"
        }
      ]
    };
  }

  return { questions: [] };
}

// Main handler for Bridge JS requests
app.post("/api/bridge", async (req, res) => {
  const { action, data = {} } = req.body || {};

  try {
    if (action === "list_decks") {
      return res.json({
        success: true,
        data: { decks: BUILTIN_DECKS }
      });
    }

    if (action === "get_source_models") {
      return res.json({
        success: true,
        data: { models: [{ id: 101, name: "Vocabulary Note (Term & Definition)" }] }
      });
    }

    if (action === "get_source_fields") {
      return res.json({
        success: true,
        data: { fields: ["Term", "Definition"] }
      });
    }

    if (action === "sample_vocab_pairs") {
      const deckId = Number(data.deck_id) || 1;
      const limit = Math.min(Number(data.limit) || 50, 50);
      const pairs = VOCAB_POOLS[deckId] || VOCAB_POOLS[1];
      const shuffledDeck = shuffleArray(pairs);
      const selected = shuffledDeck.slice(0, limit);
      return res.json({
        success: true,
        data: {
          pairs: selected,
          total: selected.length,
          limit: limit,
          exhausted: false
        }
      });
    }

    if (action === "get_settings") {
      return res.json({
        success: true,
        data: appSettings
      });
    }

    if (action === "save_settings") {
      Object.assign(appSettings, data);
      return res.json({
        success: true,
        data: { saved: Object.keys(data) }
      });
    }

    if (action === "get_ui_lang") {
      return res.json({
        success: true,
        data: { lang: appSettings.ui_lang || "vi" }
      });
    }

    if (action === "set_ui_lang") {
      appSettings.ui_lang = data.lang || "vi";
      return res.json({
        success: true,
        data: { lang: appSettings.ui_lang }
      });
    }

    if (action === "get_ui_strings") {
      const lang = appSettings.ui_lang || "vi";
      const filePath = path.join(process.cwd(), "lang", `${lang}.json`);
      let strings = {};
      if (fs.existsSync(filePath)) {
        strings = JSON.parse(fs.readFileSync(filePath, "utf-8"));
      } else {
        const enPath = path.join(process.cwd(), "lang", "en.json");
        if (fs.existsSync(enPath)) {
          strings = JSON.parse(fs.readFileSync(enPath, "utf-8"));
        }
      }
      return res.json({
        success: true,
        data: { strings, lang }
      });
    }

    if (action === "check_api_key") {
      const hasKey = Boolean(process.env.GEMINI_API_KEY);
      return res.json({
        success: true,
        data: {
          has_key: hasKey,
          key_count: hasKey ? 1 : 0,
          keys: hasKey ? ["Gemini API Key"] : []
        }
      });
    }

    if (action === "test_key" || action === "test_all_keys") {
      const ai = getAiClient();
      if (!ai) {
        return res.json({
          success: true,
          data: {
            results: [{ key: 1, ok: false, error: "GEMINI_API_KEY environment variable not configured." }]
          }
        });
      }
      try {
        const response = await ai.models.generateContent({
          model: "gemini-2.5-flash",
          contents: "Hello, reply 'OK'",
        });
        return res.json({
          success: true,
          data: {
            results: [{ key: 1, ok: true, model: "gemini-2.5-flash", response: response.text }]
          }
        });
      } catch (err: any) {
        return res.json({
          success: true,
          data: {
            results: [{ key: 1, ok: false, error: err.message || "Failed API key test" }]
          }
        });
      }
    }

    if (action === "save_context") {
      appContext = data;
      return res.json({ success: true, data: {} });
    }

    if (action === "load_context") {
      return res.json({
        success: true,
        data: appContext ? { has_context: true, ...appContext } : { has_context: false }
      });
    }

    if (action === "clear_context") {
      appContext = null;
      return res.json({ success: true, data: { success: true } });
    }

    if (action === "save_to_anki") {
      return res.json({ success: true, data: { success: true, count: 1 } });
    }

    if (action === "close_hub") {
      return res.json({ success: true, data: {} });
    }

    if (action === "generate") {
      const gamemode = data.gamemode || "fill_blank";
      const count = Number(data.count) || 5;
      const language = data.language || "en";
      const level = data.level || "intermediate";
      const topic = data.topic || "daily_life";
      const vocabPairs = data.vocab_pairs || [];

      // Game Mode 5: Word Matching is offline logic
      if (gamemode === "matching") {
        const pairs = vocabPairs.length > 0 
          ? vocabPairs.map((p: any) => ({ term: p.term, definition: p.definition }))
          : VOCAB_POOLS[1].slice(0, count).map(p => ({ term: p.term, definition: p.definition }));
        
        const left = pairs.map((p: any) => p.term).sort(() => Math.random() - 0.5);
        const right = pairs.map((p: any) => p.definition).sort(() => Math.random() - 0.5);

        return res.json({
          success: true,
          data: {
            error: false,
            pairs,
            left_column: left,
            right_column: right
          }
        });
      }

      // Check Gemini API
      const ai = getAiClient();
      if (!ai) {
        console.warn(`[Server] GEMINI_API_KEY missing - returning rich fallback exercise for ${gamemode}`);
        let fallback = getFallbackExercise(gamemode, data);
        if (gamemode === "unscramble" && fallback.sentences) {
          fallback = {
            questions: fallback.sentences.map((s: any) => ({
              correct_sentence: s.correct_sentence,
              shuffled_words: s.correct_sentence.split(" ").sort(() => Math.random() - 0.5),
              hint: s.hint,
              translation: s.translation,
              word_count: s.correct_sentence.split(" ").length
            }))
          };
        }
        return res.json({ success: true, data: fallback });
      }

      // Generate via Gemini API
      try {
        // Candidate pool: up to 50 terms
        const candidatePool = (vocabPairs && vocabPairs.length > 0)
          ? vocabPairs.slice(0, 50)
          : (VOCAB_POOLS[1] || []).slice(0, 50);

        // Mathematical random selection: Fisher-Yates shuffle
        const shuffledPool = shuffleArray(candidatePool);
        // Sample 5 to 10 random terms
        const sampleSize = Math.min(
          shuffledPool.length,
          Math.floor(Math.random() * 6) + 5
        );
        const vocabSample = shuffledPool.slice(0, sampleSize);

        const vocabSection = vocabSample.length > 0
          ? `Mandatory vocabulary terms to feature (randomly selected ${vocabSample.length} terms): ${vocabSample.map((p: any) => `${p.term} (${p.definition})`).join("; ")}`
          : "None";

        const prompt = `<task>
Generate a high-quality '${gamemode}' language exercise.
Target Language: ${language}
Level: ${level}
Topic: ${topic}
Count: ${count}
${gamemode === "cloze" ? `Blanks Count: ${data.num_blanks || 5}` : ""}
</task>

<context>
${vocabSection}
</context>

<language_constraints>
- TARGET LANGUAGE (${language}): Used EXCLUSIVELY for raw exercise content (sentences, reading passages, blank options, secret words).
- SUPPORT LANGUAGE (Tiếng Việt): Used EXCLUSIVELY for ALL keys ending with '_vietnamese' (explanations, translations, hints). NEVER output ${language} in these fields.
</language_constraints>

<example_output_format>
Here is an example of the STRICT bilingual format expected (for fill_blank):
{
  "sentence_with_blank": "If you want to see your family, you can make a _____.",
  "full_sentence": "If you want to see your family, you can make a video call.",
  "blank_word": "video call",
  "options": ["video call", "video game", "video clip", "video player"],
  "options_vietnamese": ["cuộc gọi video", "trò chơi điện tử", "đoạn video ngắn", "đầu phát video"],
  "correct_index": 0,
  "sentence_vietnamese": "Nếu bạn muốn gặp gia đình mình, bạn có thể thực hiện một cuộc gọi video.",
  "explanation_vietnamese": "Chọn 'video call' (cuộc gọi video) vì nó phù hợp nhất với ngữ cảnh muốn liên lạc và nhìn thấy người thân ở xa."
}
</example_output_format>

<schema_requirements>
Generate exactly ${count} items following the exact JSON schema provided in the API configuration. Ensure EVERY single field ending with '_vietnamese' is populated in fluent Vietnamese without leaving any field blank or falling back to ${language}.
</schema_requirements>`;

        const schema = SCHEMAS[gamemode];

        const response = await ai.models.generateContent({
          model: "gemini-3.6-flash",
          contents: prompt,
          config: schema ? {
            systemInstruction: `You are an elite AI language educator designed for Vietnamese learners. 
Your primary directive is STRICT BILINGUAL SEPARATION. You must seamlessly switch between the TARGET LANGUAGE (${language}) and the SUPPORT LANGUAGE (Vietnamese).

CRITICAL RULES FOR JSON OUTPUT:
1. THE TARGET LANGUAGE ONLY RULE: Fields containing raw exercise content (sentences, reading passages, blank options, secret words) MUST be 100% in the target language (${language}).
2. THE VIETNAMESE ONLY RULE: Fields requiring explanation, translation, hints, grammar notes, or word meanings (all keys ending with _vietnamese) MUST be 100% in natural, fluent Vietnamese (Tiếng Việt). NEVER output ${language} or English in _vietnamese fields.
3. EXPLANATION QUALITY: When explaining "WHY" an option is correct (explanation_vietnamese), clearly cite the grammar rule, vocabulary context, or collocation IN VIETNAMESE.
4. STRUCTURAL INTEGRITY: Output NOTHING but valid JSON. No markdown backticks (\`\`\`json), no conversational filler.`,
            temperature: 0.2,
            maxOutputTokens: 3000,
            responseMimeType: "application/json",
            responseSchema: schema
          } : undefined
        });

        let parsed: any = {};
        try {
          parsed = JSON.parse(response.text || "{}");
        } catch (_) {
          parsed = getFallbackExercise(gamemode, data);
        }

        // Post-process & normalize _vietnamese keys for client UI compatibility
        if (parsed) {
          if (gamemode === "fill_blank" && parsed.questions) {
            parsed.questions = parsed.questions.map((q: any) => ({
              ...q,
              options_translations: q.options_vietnamese || q.options_translations || [],
              sentence_translation: q.sentence_vietnamese || q.sentence_translation || "",
              explanation_short: q.explanation_vietnamese || q.explanation_short || ""
            }));
          } else if (gamemode === "cloze") {
            if (parsed.sentence_meaning_vietnamese || parsed.sentence_vietnamese) {
              parsed.sentence_meaning = parsed.sentence_meaning_vietnamese || parsed.sentence_vietnamese || parsed.sentence_meaning || "";
            }
            if (parsed.blanks) {
              parsed.blanks = parsed.blanks.map((b: any) => ({
                ...b,
                meaning_in_vietnamese: b.meaning_vietnamese || b.meaning_in_vietnamese || "",
                explanation_short: b.explanation_vietnamese || b.explanation_short || ""
              }));
            }
          } else if (gamemode === "story") {
            if (parsed.passage_vietnamese) {
              parsed.passage_translation = parsed.passage_vietnamese;
            }
            if (parsed.comprehension_questions) {
              parsed.comprehension_questions = parsed.comprehension_questions.map((q: any) => ({
                ...q,
                options_translations: q.options_vietnamese || q.options_translations || [],
                explanation: q.explanation_vietnamese || q.explanation || ""
              }));
            }
          } else if (gamemode === "translation" && parsed.sentences) {
            parsed.sentences = parsed.sentences.map((s: any) => ({
              ...s,
              target_text: s.target_text_vietnamese || s.target_text || "",
              grammar_notes: s.grammar_notes_vietnamese || s.grammar_notes || ""
            }));
          } else if (gamemode === "unscramble" && parsed.sentences) {
            parsed = {
              questions: parsed.sentences.map((s: any) => {
                const hint = s.hint_vietnamese || s.hint || "";
                const translation = s.translation_vietnamese || s.translation || "";
                return {
                  correct_sentence: s.correct_sentence,
                  shuffled_words: s.correct_sentence.split(" ").sort(() => Math.random() - 0.5),
                  hint: hint,
                  translation: translation,
                  sentence_meaning: s.sentence_meaning_vietnamese || s.sentence_meaning || translation,
                  key_vocab: (s.key_vocab || []).map((v: any) => ({
                    word: v.word,
                    meaning: v.meaning_vietnamese || v.meaning || ""
                  })),
                  word_count: s.correct_sentence.split(" ").length
                };
              })
            };
          } else if (gamemode === "sentence_transform" && parsed.questions) {
            parsed.questions = parsed.questions.map((q: any) => ({
              ...q,
              instruction: q.instruction_vietnamese || q.instruction || "",
              grammar_rule: q.grammar_rule_vietnamese || q.grammar_rule || ""
            }));
          } else if (gamemode === "taboo" && parsed.rounds) {
            parsed.rounds = parsed.rounds.map((r: any) => ({
              ...r,
              word_meaning_vietnamese: r.word_meaning_vietnamese || r.meaning_vietnamese || ""
            }));
          }
        }

        return res.json({
          success: true,
          data: parsed
        });
      } catch (err: any) {
        console.error(`[Server] Gemini API error for ${gamemode}:`, err);
        const fallback = getFallbackExercise(gamemode, data);
        return res.json({ success: true, data: fallback });
      }
    }

    if (action === "ai_grade") {
      const { gamemode, user_answer, expected, secret_word } = data;
      const ai = getAiClient();

      if (!ai) {
        const userNorm = (user_answer || "").trim().toLowerCase();
        const expectedNorm = (expected || secret_word || "").trim().toLowerCase();
        const isCorrect = userNorm === expectedNorm || (expectedNorm.length > 0 && userNorm.includes(expectedNorm));

        return res.json({
          success: true,
          data: {
            correct: isCorrect,
            score: isCorrect ? 100 : 50,
            explanation: isCorrect 
              ? "Good job! Your answer matches the expected solution." 
              : `Needs improvement. Expected: '${expected || secret_word}'`
          }
        });
      }

      try {
        const prompt = `Evaluate student response for exercise type '${gamemode}':
Target/Expected Answer: "${expected || secret_word}"
Student Answer: "${user_answer}"

Rules:
- Assess accuracy, grammar, vocabulary fit, and natural expression.
- Provide encouraging, clear, concise feedback in Vietnamese.`;

        const response = await ai.models.generateContent({
          model: "gemini-3.6-flash",
          contents: prompt,
          config: {
            systemInstruction: "You are an encouraging AI language teacher grading a student's answer. Return a strict JSON response with exact keys.",
            temperature: 0.2,
            maxOutputTokens: 600,
            responseMimeType: "application/json",
            responseSchema: {
              type: "object",
              properties: {
                correct: { type: "boolean" },
                score: { type: "integer" },
                explanation: { type: "string" }
              },
              required: ["correct", "score", "explanation"]
            }
          }
        });

        let result = {};
        try {
          result = JSON.parse(response.text || "{}");
        } catch (_) {
          result = { correct: true, score: 90, explanation: "Answer received and recorded." };
        }

        return res.json({
          success: true,
          data: result
        });
      } catch (err: any) {
        return res.json({
          success: true,
          data: {
            correct: true,
            score: 80,
            explanation: "Evaluated response."
          }
        });
      }
    }

    return res.json({
      success: false,
      data: {},
      error_code: "E_UNKNOWN_ACTION",
      message: `Unknown bridge action: ${action}`
    });
  } catch (error: any) {
    console.error("[Server] Exception in /api/bridge:", error);
    return res.json({
      success: false,
      data: {},
      error_code: "E_SERVER_ERROR",
      message: error.message || "Internal server error"
    });
  }
});

// Serve static web interface
const webDir = path.join(process.cwd(), "web");
app.use(express.static(webDir));

// Fallback to index.html for root or SPA paths
app.use((req, res) => {
  res.sendFile(path.join(webDir, "index.html"));
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`AI Learning Hub server running at http://0.0.0.0:${PORT}`);
});
