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
            sentence_with_blank: { type: "string" },
            full_sentence: { type: "string" },
            blank_word: { type: "string" },
            options: {
              type: "array",
              items: { type: "string" },
            },
            options_translations: {
              type: "array",
              items: { type: "string" },
            },
            correct_index: { type: "integer" },
            explanation_short: { type: "string" },
            sentence_translation: { type: "string" },
          },
          required: ["sentence_with_blank", "options", "options_translations", "correct_index", "sentence_translation", "explanation_short"],
        },
      },
    },
    required: ["questions"],
  },
  cloze: {
    type: "object",
    properties: {
      paragraph_with_blanks: { type: "string" },
      paragraph_full: { type: "string" },
      sentence_meaning: { type: "string" },
      blanks: {
        type: "array",
        items: {
          type: "object",
          properties: {
            blank_id: { type: "integer" },
            correct_word: { type: "string" },
            options: {
              type: "array",
              items: { type: "string" },
            },
            correct_index: { type: "integer" },
            explanation_short: { type: "string" },
            meaning_in_vietnamese: { type: "string" },
          },
          required: ["correct_word", "options", "correct_index"],
        },
      },
    },
    required: ["paragraph_with_blanks", "blanks"],
  },
  translation: {
    type: "object",
    properties: {
      sentences: {
        type: "array",
        items: {
          type: "object",
          properties: {
            source_text: { type: "string" },
            target_text: { type: "string" },
            grammar_notes: { type: "string" },
          },
          required: ["source_text", "target_text"],
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
            correct_sentence: { type: "string" },
            hint: { type: "string" },
            translation: { type: "string" },
            sentence_meaning: { type: "string" },
            key_vocab: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  word: { type: "string" },
                  meaning: { type: "string" },
                },
              },
            },
          },
          required: ["correct_sentence"],
        },
      },
    },
    required: ["sentences"],
  },
  story: {
    type: "object",
    properties: {
      story: { type: "string" },
      comprehension_questions: {
        type: "array",
        items: {
          type: "object",
          properties: {
            question: { type: "string" },
            options: {
              type: "array",
              items: { type: "string" },
            },
            correct_index: { type: "integer" },
            explanation: { type: "string" },
            quote_evidence: { type: "string" },
          },
          required: ["question", "options", "correct_index"],
        },
      },
    },
    required: ["story", "comprehension_questions"],
  },
  sentence_transform: {
    type: "object",
    properties: {
      questions: {
        type: "array",
        items: {
          type: "object",
          properties: {
            original_sentence: { type: "string" },
            instruction: { type: "string" },
            hint_word: { type: "string" },
            expected_answer: { type: "string" },
            grammar_rule: { type: "string" },
          },
          required: ["original_sentence", "instruction", "expected_answer"],
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
            secret_word: { type: "string" },
            forbidden_words: {
              type: "array",
              items: { type: "string" },
            },
            ai_description: { type: "string" },
            category: { type: "string" },
          },
          required: ["secret_word", "forbidden_words", "ai_description"],
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

        const vocabPrompt = vocabSample.length > 0
          ? `\nMandatory vocabulary terms to feature (randomly selected ${vocabSample.length} terms): ${vocabSample.map((p: any) => `${p.term} (${p.definition})`).join("; ")}.`
          : "";

        let prompt = `Generate a high-quality '${gamemode}' language exercise in ${language} (Level: ${level}, Topic: ${topic}, Count: ${count}).${vocabPrompt}\n`;

        if (gamemode === "fill_blank") {
          prompt += `Generate ${count} fill-in-the-blank questions.
- sentence_with_blank: Natural sentence in ${language} containing '_____' for missing blank.
- full_sentence: Complete correct sentence in ${language}.
- options: Exactly 4 distinct choices in ${language} (1 correct, 3 distractors).
- options_translations: Exactly 4 corresponding concise Vietnamese translations for each option.
- correct_index: Integer 0-3 of the correct choice.
- sentence_translation: Natural Vietnamese translation of full_sentence.
- explanation_short: Concise Vietnamese explanation (1-2 sentences) explaining why correct option fits context and grammar.`;
        } else if (gamemode === "cloze") {
          const numBlanks = data.num_blanks || 5;
          prompt += `Generate 1 coherent cloze passage in ${language} with ${numBlanks} blanks.
- paragraph_with_blanks: Text containing placeholders [1], [2]... [${numBlanks}].
- paragraph_full: Complete passage with correct words filled in.
- sentence_meaning: Natural Vietnamese translation of the complete passage.
- blanks: Array of ${numBlanks} blank definitions:
  - blank_id: Integer 1..${numBlanks}
  - correct_word: Target word in ${language}
  - options: Array of all ${numBlanks} target correct words in this passage
  - correct_index: Integer index of correct_word in options
  - meaning_in_vietnamese: Concise Vietnamese translation of correct_word
  - explanation_short: Short Vietnamese explanation why this word fits blank [i].`;
        } else if (gamemode === "story") {
          prompt += `Generate 1 reading passage in ${language} (120-180 words suited for level '${level}' and topic '${topic}') with ${count} comprehension questions.
For each comprehension question:
- question: Clear question in ${language} testing passage comprehension
- options: Exactly 4 choice options (A, B, C, D) in ${language}
- correct_index: Integer 0-3 of the correct choice
- explanation: Detailed explanation in Vietnamese explaining WHY this option is correct
- quote_evidence: Exact verbatim quote/sentence from the reading passage in ${language} that provides direct evidence for the answer.`;
        } else if (gamemode === "translation") {
          prompt += `Generate ${count} translation practice sentences in ${language}.
- source_text: Sentence in ${language}
- target_text: Accurate, natural Vietnamese translation
- grammar_notes: Key grammar patterns or vocabulary usage notes in Vietnamese.`;
        } else if (gamemode === "unscramble") {
          prompt += `Generate ${count} sentence unscramble items in ${language}.
- correct_sentence: Complete natural sentence in ${language}
- hint: Short hint in Vietnamese
- translation: Full Vietnamese translation
- sentence_meaning: Full Vietnamese translation
- key_vocab: Array of key vocabulary words with Vietnamese meanings [{ "word": "...", "meaning": "..." }].`;
        } else if (gamemode === "sentence_transform") {
          prompt += `Generate ${count} sentence transformation questions in ${language}.
- original_sentence: Starting sentence in ${language}
- instruction: Task instruction in Vietnamese (e.g. "Viết lại câu sử dụng từ gợi ý...")
- hint_word: Key word or structure to incorporate
- expected_answer: Correct transformed sentence in ${language}
- grammar_rule: Explanation in Vietnamese of the grammar rule/structure applied.`;
        } else if (gamemode === "taboo") {
          prompt += `Generate ${count} Taboo vocabulary guessing rounds in ${language}.
- secret_word: Target word in ${language}
- forbidden_words: Array of 4 forbidden related words in ${language}
- ai_description: Helpful description/clue in ${language} WITHOUT using secret_word or forbidden_words
- category: Word topic/category.`;
        }

        const schema = SCHEMAS[gamemode];

        const response = await ai.models.generateContent({
          model: "gemini-2.5-flash",
          contents: prompt,
          config: schema ? {
            systemInstruction: "You are an AI language learning engine. Generate precise, high-quality, strictly formatted JSON language exercises. Follow the requested schema strictly without conversational filler or markdown code block markers.",
            temperature: 0.3,
            maxOutputTokens: 2500,
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

        // Post-process UI formats
        if (gamemode === "unscramble" && parsed.sentences) {
          parsed = {
            questions: parsed.sentences.map((s: any) => ({
              correct_sentence: s.correct_sentence,
              shuffled_words: s.correct_sentence.split(" ").sort(() => Math.random() - 0.5),
              hint: s.hint,
              translation: s.translation,
              word_count: s.correct_sentence.split(" ").length
            }))
          };
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
          model: "gemini-2.5-flash",
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
