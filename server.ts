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

// Schemas for Gemini Structured Output (v2 — matches Pydantic models in schema_registry.py)
const SCHEMAS: Record<string, any> = {
  fill_blank: {
    type: "object",
    properties: {
      questions: {
        type: "array",
        items: {
          type: "object",
          properties: {
            sentence: { type: "string" },
            target_word: { type: "string" },
            meaning_vi: { type: "string" },
            full_translation: { type: "string" },
            options: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  word: { type: "string" },
                  is_correct: { type: "boolean" },
                  type: { type: "string" },
                  reason: { type: "string" }
                },
                required: ["word", "is_correct", "type", "reason"]
              }
            },
            explanation: { type: "string" },
            grammar_note: { type: "string" }
          },
          required: ["sentence", "target_word", "meaning_vi", "full_translation", "options", "explanation"]
        }
      }
    },
    required: ["questions"]
  },
  cloze: {
    type: "object",
    properties: {
      paragraph: { type: "string" },
      full_solution_text: { type: "string" },
      story_translation: { type: "string" },
      context_summary: { type: "string" },
      blanks: {
        type: "array",
        items: {
          type: "object",
          properties: {
            id: { type: "string" },
            answer: { type: "string" },
            meaning_vi: { type: "string" },
            hint: { type: "string" },
            distractors: {
              type: "array",
              items: { type: "string" }
            },
            explanation: { type: "string" }
          },
          required: ["id", "answer", "meaning_vi", "hint", "explanation"]
        }
      }
    },
    required: ["paragraph", "full_solution_text", "story_translation", "context_summary", "blanks"]
  },
  translation: {
    type: "object",
    properties: {
      source_sentence: { type: "string" },
      target_language: { type: "string" },
      reference_translation: { type: "string" },
      alternative_translations: {
        type: "array",
        items: {
          type: "object",
          properties: {
            text: { type: "string" },
            note: { type: "string" }
          },
          required: ["text", "note"]
        }
      },
      key_vocabulary: {
        type: "array",
        items: {
          type: "object",
          properties: {
            source: { type: "string" },
            target: { type: "string" },
            note: { type: "string" }
          },
          required: ["source", "target", "note"]
        }
      },
      common_mistakes: {
        type: "array",
        items: {
          type: "object",
          properties: {
            wrong: { type: "string" },
            error_type: { type: "string" },
            correction: { type: "string" }
          },
          required: ["wrong", "error_type", "correction"]
        }
      },
      grading_rubric: { type: "string" }
    },
    required: ["source_sentence", "target_language", "reference_translation", "alternative_translations", "key_vocabulary", "common_mistakes", "grading_rubric"]
  },
  unscramble: {
    type: "object",
    properties: {
      questions: {
        type: "array",
        items: {
          type: "object",
          properties: {
            correct_sentence: { type: "string" },
            meaning_vi: { type: "string" },
            hint: { type: "string" },
            key_vocabulary: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  word: { type: "string" },
                  meaning_vi: { type: "string" }
                },
                required: ["word", "meaning_vi"]
              }
            },
            difficulty_reason: { type: "string" },
            grammar_note: { type: "string" }
          },
          required: ["correct_sentence", "meaning_vi", "hint", "key_vocabulary", "difficulty_reason", "grammar_note"]
        }
      }
    },
    required: ["questions"]
  },
  story: {
    type: "object",
    properties: {
      story: {
        type: "object",
        properties: {
          title: { type: "string" },
          content: { type: "string" },
          word_count: { type: "integer" },
          highlighted_vocab: {
            type: "array",
            items: {
              type: "object",
              properties: {
                word: { type: "string" },
                meaning_vi: { type: "string" },
                context_meaning: { type: "string" }
              },
              required: ["word", "meaning_vi", "context_meaning"]
            }
          },
          full_translation: { type: "string" }
        },
        required: ["title", "content", "word_count", "highlighted_vocab", "full_translation"]
      },
      questions: {
        type: "array",
        items: {
          type: "object",
          properties: {
            id: { type: "integer" },
            type: { type: "string" },
            question: { type: "string" },
            options: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  text: { type: "string" },
                  is_correct: { type: "boolean" }
                },
                required: ["text", "is_correct"]
              }
            },
            explanation: { type: "string" },
            evidence_quote: { type: "string" }
          },
          required: ["id", "type", "question", "options", "explanation", "evidence_quote"]
        }
      },
      discussion_prompt: { type: "string" }
    },
    required: ["story", "questions", "discussion_prompt"]
  },
  sentence_transform: {
    type: "object",
    properties: {
      questions: {
        type: "array",
        items: {
          type: "object",
          properties: {
            original: { type: "string" },
            prompt: { type: "string" },
            expected_answer: { type: "string" },
            normalized_answer: { type: "string" },
            acceptable_variations: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  text: { type: "string" },
                  note: { type: "string" }
                },
                required: ["text", "note"]
              }
            },
            forbidden_words: {
              type: "array",
              items: { type: "string" }
            },
            grammar_rule: { type: "string" },
            common_errors: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  error: { type: "string" },
                  feedback: { type: "string" }
                },
                required: ["error", "feedback"]
              }
            }
          },
          required: ["original", "prompt", "expected_answer", "normalized_answer", "acceptable_variations", "forbidden_words", "grammar_rule", "common_errors"]
        }
      }
    },
    required: ["questions"]
  },
  taboo: {
    type: "object",
    properties: {
      rounds: {
        type: "array",
        items: {
          type: "object",
          properties: {
            target_word: { type: "string" },
            meaning_vi: { type: "string" },
            taboo_words: {
              type: "array",
              items: { type: "string" }
            },
            clue: { type: "string" },
            difficulty_level: { type: "string" },
            sample_acceptable_phrases: {
              type: "array",
              items: { type: "string" }
            },
            sample_forbidden_phrases: {
              type: "array",
              items: { type: "string" }
            }
          },
          required: ["target_word", "meaning_vi", "taboo_words", "clue", "difficulty_level", "sample_acceptable_phrases", "sample_forbidden_phrases"]
        }
      }
    },
    required: ["rounds"]
  }
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

// XSS Sanitization helper for AI content
function sanitizeHtml(htmlContent: string): string {
  if (!htmlContent || typeof htmlContent !== "string") return htmlContent || "";
  let clean = htmlContent.replace(/<(script|iframe|object|embed|style|link|form|input|button)\b[^<]*(?:(?!<\/\1>)<[^<]*)*<\/\1>/gi, "");
  clean = clean.replace(/<(script|iframe|object|embed|style|link|form|input|button)\b[^>]*\/?>/gi, "");
  clean = clean.replace(/\s*on\w+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)/gi, "");
  clean = clean.replace(/(href|src|action)\s*=\s*["']?\s*javascript:[^"'>]*["']?/gi, "");
  return clean;
}

function sanitizeAiOutput<T>(data: T): T {
  if (data === null || data === undefined) return data;
  if (typeof data === "string") {
    return sanitizeHtml(data) as unknown as T;
  }
  if (Array.isArray(data)) {
    return data.map(item => sanitizeAiOutput(item)) as unknown as T;
  }
  if (typeof data === "object") {
    const cleanObj: Record<string, any> = {};
    for (const key of Object.keys(data as object)) {
      cleanObj[key] = sanitizeAiOutput((data as Record<string, any>)[key]);
    }
    return cleanObj as T;
  }
  return data;
}

function normalizeAnswer(text: string): string {
  if (!text) return "";
  return text.trim().toLowerCase().normalize("NFKD")
    .replace(/[.,!?;:]+$/g, "")
    .replace(/\s+/g, " ");
}

// Fallback Generators when API Key is not configured or fails (v2 format)
function getFallbackExercise(gamemode: string, data: any) {
  const count = data.count || 3;

  if (gamemode === "fill_blank") {
    return {
      questions: Array.from({ length: count }, (_, i) => ({
        sentence: "Smartphones have become _____ in modern daily life.",
        target_word: "ubiquitous",
        meaning_vi: "phổ biến khắp nơi",
        full_translation: "Điện thoại thông minh đã trở nên phổ biến khắp nơi trong cuộc sống hiện đại.",
        options: [
          { word: "ubiquitous", is_correct: true, type: "correct", reason: "Chính xác! 'ubiquitous' có nghĩa là phổ biến khắp nơi." },
          { word: "ephemeral", is_correct: false, type: "antonym", reason: "Không phù hợp: 'ephemeral' có nghĩa là ngắn ngủi, tạm thời." },
          { word: "pragmatic", is_correct: false, type: "wrong_context", reason: "Không phù hợp: 'pragmatic' có nghĩa là thực tế, thiết thực." },
          { word: "ubiquitously", is_correct: false, type: "different_word_class", reason: "Không phù hợp: 'ubiquitously' là trạng từ, trong khi sau động từ 'become' cần một tính từ." }
        ],
        explanation: "Chọn 'ubiquitous' vì ngữ cảnh mô tả điện thoại thông minh xuất hiện ở khắp mọi nơi.",
        grammar_note: "Cấu trúc: 'become + adjective' (trở nên như thế nào)."
      }))
    };
  }

  if (gamemode === "cloze") {
    return {
      paragraph: "In today's fast-paced world, clear communication is essential. Being [BLANK_1] allows professionals to express complex ideas effectively. When teams face difficult challenges, reaching a [BLANK_2] ensures everyone works toward the same goal. Having a [BLANK_3] approach helps resolve conflicts quickly.",
      full_solution_text: "In today's fast-paced world, clear communication is essential. Being articulate allows professionals to express complex ideas effectively. When teams face difficult challenges, reaching a consensus ensures everyone works toward the same goal. Having a pragmatic approach helps resolve conflicts quickly.",
      story_translation: "Trong thế giới hiện đại, giao tiếp rõ ràng là rất quan trọng.",
      context_summary: "Đoạn văn nói về tầm quan trọng của giao tiếp rõ ràng trong công việc.",
      blanks: [
        {
          id: "BLANK_1",
          answer: "articulate",
          meaning_vi: "diễn đạt lưu loát",
          hint: "Khả năng nói hoặc viết một cách rõ ràng và dễ hiểu",
          distractors: [],
          explanation: "'articulate' có nghĩa là diễn đạt rõ ràng, phù hợp với ngữ cảnh giao tiếp chuyên nghiệp."
        },
        {
          id: "BLANK_2",
          answer: "consensus",
          meaning_vi: "sự đồng thuận",
          hint: "Sự nhất trí chung của một nhóm người",
          distractors: [],
          explanation: "'consensus' là sự đồng thuận giữa các thành viên trong nhóm."
        },
        {
          id: "BLANK_3",
          answer: "pragmatic",
          meaning_vi: "thực tế",
          hint: "Cách tiếp cận dựa trên thực tiễn",
          distractors: [],
          explanation: "'pragmatic' là cách tiếp cận thực tế để giải quyết vấn đề."
        }
      ]
    };
  }

  if (gamemode === "translation") {
    return {
      source_sentence: "Việc sử dụng công nghệ một cách thực tế giúp cải thiện hiệu suất công việc.",
      target_language: "en",
      reference_translation: "Using technology pragmatically helps improve work performance.",
      alternative_translations: [
        { text: "Applying technology in a practical way enhances productivity.", note: "Trang trọng hơn" }
      ],
      key_vocabulary: [
        { source: "sử dụng công nghệ", target: "use technology", note: "Cụm động từ" },
        { source: "hiệu suất công việc", target: "work performance", note: "Danh từ ghép" }
      ],
      common_mistakes: [
        { wrong: "use technology pragmatic", error_type: "Grammar", correction: "Cần dùng trạng từ 'pragmatically' để bổ nghĩa cho động từ 'use'." }
      ],
      grading_rubric: "Đánh giá dựa trên độ chính xác ngữ pháp và sự tự nhiên của bản dịch."
    };
  }

  if (gamemode === "unscramble") {
    return {
      questions: [
        {
          correct_sentence: "Technology plays an important role in modern education.",
          meaning_vi: "Công nghệ đóng vai trò quan trọng trong giáo dục hiện đại.",
          hint: "Vai trò của công nghệ",
          key_vocabulary: [
            { word: "education", meaning_vi: "giáo dục" },
            { word: "important role", meaning_vi: "vai trò quan trọng" }
          ],
          difficulty_reason: "Cấu trúc S-V-O cơ bản với cụm giới từ.",
          grammar_note: "Sử dụng cụm danh từ 'modern education' đứng sau giới từ 'in'."
        }
      ]
    };
  }

  if (gamemode === "story") {
    const content = "Alex was known for his articulate presentation style. During the annual conference, he presented a comprehensive plan to mitigate operational risks. Despite initial skepticism from the board, his persuasive arguments helped the team reach a unanimous consensus on the new strategic paradigm.";
    return {
      story: {
        title: "Alex's Persuasive Speech",
        content,
        word_count: content.split(" ").length,
        highlighted_vocab: [
          { word: "articulate", meaning_vi: "diễn đạt trôi chảy, rõ ràng", context_meaning: "Cách nói rõ ràng và thu hút người nghe" }
        ],
        full_translation: "Alex nổi tiếng với phong cách thuyết trình diễn đạt lưu loát và rõ ràng."
      },
      questions: [
        {
          id: 1,
          type: "detail",
          question: "What was Alex known for during presentations?",
          options: [
            { text: "His articulate style", is_correct: true },
            { text: "His verbose explanations", is_correct: false },
            { text: "His ambiguous slides", is_correct: false },
            { text: "His hesitant tone", is_correct: false }
          ],
          explanation: "Alex nổi tiếng với phong cách thuyết trình diễn đạt lưu loát và rõ ràng (articulate presentation style).",
          evidence_quote: "Alex was known for his articulate presentation style."
        }
      ],
      discussion_prompt: "Thảo luận về tầm quan trọng của việc thuyết trình rõ ràng trong công việc."
    };
  }

  if (gamemode === "sentence_transform") {
    return {
      questions: [
        {
          original: "They built the new bridge in less than six months.",
          prompt: "Rewrite using the passive voice (start with 'The new bridge...').",
          expected_answer: "The new bridge was built in less than six months.",
          normalized_answer: "the new bridge was built in less than six months",
          acceptable_variations: [
            { text: "The new bridge was built in under six months.", note: "Sử dụng 'under' thay cho 'less than'" }
          ],
          forbidden_words: ["they"],
          grammar_rule: "Passive voice in Simple Past: Subject + was/were + Past Participle",
          common_errors: [
            { error: "The new bridge is built in less than six months.", feedback: "Sai thì: câu gốc dùng 'built' ở quá khứ đơn, nên câu bị động phải dùng 'was built'." }
          ]
        }
      ]
    };
  }

  if (gamemode === "taboo") {
    return {
      rounds: [
        {
          target_word: "UBIQUITOUS",
          meaning_vi: "phổ biến khắp nơi",
          taboo_words: ["EVERYWHERE", "COMMON", "FOUND", "PRESENT", "ALWAYS"],
          clue: "Describing something that seems to exist in all places at the same time, like modern technology or mobile phones.",
          difficulty_level: "Medium",
          sample_acceptable_phrases: ["present in all places", "found everywhere"],
          sample_forbidden_phrases: ["always common everywhere"]
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



    if (action === "save_to_anki") {
      return res.json({ success: true, data: { success: true, count: 1 } });
    }

    if (action === "close_hub") {
      return res.json({ success: true, data: {} });
    }

    if (action === "generate") {
      const gamemode = data.gamemode || "fill_blank";
      const rawCount = Number(data.count) || 5;
      const count = Math.max(1, Math.min(rawCount, 15)); // Clamp between 1 and 15
      const language = String(data.language || "en").substring(0, 20);
      const level = String(data.level || "intermediate").substring(0, 30);
      const topic = String(data.topic || "daily_life").substring(0, 100);
      const vocabPairs = Array.isArray(data.vocab_pairs) ? data.vocab_pairs : [];

      // Game Mode 5: Word Matching is offline logic
      if (gamemode === "matching") {
        const rawPairs = vocabPairs.length > 0 
          ? vocabPairs.map((p: any) => ({ term: p.term || p.word || "", definition: p.definition || p.meaning || "" }))
          : VOCAB_POOLS[1].slice(0, count).map(p => ({ term: p.term, definition: p.definition }));
        
        const count_pairs = Math.min(count, rawPairs.length);
        const selected = shuffleArray(rawPairs).slice(0, count_pairs);
        const gameId = `match_${Math.random().toString(36).substring(2, 9)}`;
        const items: Array<{id: string, content: string, type: string, pair_id: string}> = [];
        selected.forEach((p: any, idx: number) => {
          const pid = `pair_${idx + 1}`;
          items.push({ id: `t${idx}`, content: p.term, type: "term", pair_id: pid });
          items.push({ id: `d${idx}`, content: p.definition, type: "definition", pair_id: pid });
        });

        return res.json({
          success: true,
          data: {
            game_id: gameId,
            items: shuffleArray(items),
            config: { total_pairs: count_pairs, time_limit_sec: 120 },
            metadata: { topic: data.topic || "vocabulary", level: data.level || "intermediate" }
          }
        });
      }

      // Check Gemini API
      const ai = getAiClient();
      if (!ai) {
        console.warn(`[Server] GEMINI_API_KEY missing - returning rich fallback exercise for ${gamemode}`);
        const fallback = getFallbackExercise(gamemode, data);
        return res.json({
          success: true,
          data: {
            ...fallback,
            is_fallback: true,
            fallback_reason: "Chưa cấu hình GEMINI_API_KEY. Đang sử dụng bài tập mẫu."
          }
        });
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

<language_rule>
- Fields containing exercise content (sentences, passages, options, target words, clues) MUST be in the TARGET LANGUAGE (${language}).
- Fields ending with '_vi' (meaning_vi, full_translation, story_translation, explanation) MUST be in Vietnamese (Tiếng Việt).
- All other fields follow the schema specification.
</language_rule>

<schema_requirements>
Generate exactly ${count} items following the exact JSON schema provided in the API configuration.
</schema_requirements>`;

        const schema = SCHEMAS[gamemode];

        const response = await ai.models.generateContent({
          model: "gemini-flash-latest",
          contents: prompt,
          config: schema ? {
            systemInstruction: `You are an elite AI language educator. You output ONLY valid JSON matching the provided schema.

LANGUAGE RULES:
1. Content in ${language}: sentences, passages, options, target words, clues, expected answers
2. Vietnamese (_vi fields): meaning_vi, full_translation, story_translation, explanation, grammar_note, hint, context_summary

STRUCTURAL RULES:
- Output ONLY raw JSON. No markdown, no backticks, no conversational text.`,
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

        // Sanitize AI Output to prevent XSS
        parsed = sanitizeAiOutput(parsed);

        // v2 post-processing: minimal — ensure shuffled_words for unscramble
        if (gamemode === "unscramble" && parsed.questions) {
          parsed.questions = parsed.questions.map((q: any) => ({
            ...q,
            shuffled_words: q.correct_sentence ? q.correct_sentence.split(" ").sort(() => Math.random() - 0.5) : []
          }));
        }

        // Shuffle options for fill_blank game mode
        if (gamemode === "fill_blank" && parsed.questions) {
          parsed.questions = parsed.questions.map((q: any) => {
            if (!q.options || !Array.isArray(q.options)) return q;
            const originalOptions = [...q.options];
            const shuffledOptions = originalOptions
              .map((value) => ({ value, sort: Math.random() }))
              .sort((a, b) => a.sort - b.sort)
              .map(({ value }) => value);
            
            const correctIndex = shuffledOptions.findIndex((o: any) => typeof o === "object" ? o.is_correct : false);
            return {
              ...q,
              options: shuffledOptions,
              correct_index: correctIndex
            };
          });
        }

        // Shuffle options for story game mode
        if (gamemode === "story" && parsed.questions) {
          parsed.questions = parsed.questions.map((q: any) => {
            if (!q.options || !Array.isArray(q.options)) return q;
            const originalOptions = [...q.options];
            const shuffledOptions = originalOptions
              .map((value) => ({ value, sort: Math.random() }))
              .sort((a, b) => a.sort - b.sort)
              .map(({ value }) => value);
            
            const correctIndex = shuffledOptions.findIndex((o: any) => typeof o === "object" ? o.is_correct : false);
            return {
              ...q,
              options: shuffledOptions,
              correct_index: correctIndex
            };
          });
        }

        return res.json({
          success: true,
          data: parsed
        });
      } catch (err: any) {
        console.error(`[Server] Gemini API error for ${gamemode}:`, err);
        const fallback = getFallbackExercise(gamemode, data);
        const isQuotaError = err?.status === 429 || String(err?.message || "").includes("429") || String(err?.message || "").includes("quota");
        const reasonMsg = isQuotaError
          ? "Đã vượt quá hạn ngạch AI (429 Rate Limit). Đang tự động chuyển sang bài tập mẫu."
          : "Lỗi kết nối Gemini AI. Đang tự động chuyển sang bài tập mẫu.";
        return res.json({
          success: true,
          data: {
            ...fallback,
            is_fallback: true,
            fallback_reason: reasonMsg
          }
        });
      }
    }

    if (action === "ai_grade") {
      const { gamemode, user_answer, expected_answer, target_word } = data;
      const targetAns = expected_answer || target_word || "";

      const uNorm = normalizeAnswer(user_answer);
      const tNorm = normalizeAnswer(targetAns);
      const isExactMatch = uNorm.length > 0 && uNorm === tNorm;

      const ai = getAiClient();

      if (!ai || isExactMatch) {
        const isCorrect = isExactMatch || (tNorm.length > 0 && (uNorm.includes(tNorm) || tNorm.includes(uNorm)));

        return res.json({
          success: true,
          data: {
            correct: isCorrect,
            score: isExactMatch ? 100 : (isCorrect ? 85 : 40),
            explanation: isExactMatch
              ? "Xuất sắc! Câu trả lời hoàn toàn chính xác."
              : isCorrect
                ? `Khá tốt! Đáp án gợi ý: '${targetAns}'`
                : `Cần cải thiện. Đáp án chính xác: '${targetAns}'`
          }
        });
      }

      try {
        const prompt = `Evaluate student response for exercise type '${gamemode}':
Target/Expected Answer: "${targetAns}"
Student Answer: "${user_answer}"

Rules:
- Be flexible with minor punctuation or capitalization variations.
- Assess accuracy, grammar, vocabulary fit, and natural expression.
- Provide encouraging, clear, concise feedback in Vietnamese.`;

        const response = await ai.models.generateContent({
          model: "gemini-flash-latest",
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
          result = { correct: true, score: 90, explanation: "Đã nhận và lưu câu trả lời." };
        }

        result = sanitizeAiOutput(result);

        return res.json({
          success: true,
          data: result
        });
      } catch (err: any) {
        console.error("[Server] Error during ai_grade:", err?.message || err);
        const isPartial = tNorm.length > 0 && (uNorm.includes(tNorm) || tNorm.includes(uNorm));
        return res.json({
          success: true,
          data: {
            correct: isPartial,
            score: isPartial ? 80 : 40,
            explanation: isPartial
              ? `Câu trả lời khá sát. Đáp án gợi ý: '${targetAns}'`
              : `Đáp án gợi ý: '${targetAns}'`
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
