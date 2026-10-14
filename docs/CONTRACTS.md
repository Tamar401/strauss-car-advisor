# חוזים בין השכבות

מקור האמת הוא `backend/app/contracts.py`. המסמך הזה מסביר אותו. משנים חוזה רק בהסכמה של שתיכן, ומריצים `pytest` אחרי כל שינוי.

## נתיבים

| נתיב | מצב | בעלות | מחזיר |
|---|---|---|---|
| `GET /api/catalog` | אמיתי | משותף | `list[Car]` |
| `GET /api/occupations` | אמיתי | משותף | `list[Occupation]` |
| `GET /api/demo-employees` | אמיתי | משותף | 6 העובדים לדוגמה, בלי ת״ז |
| `GET /api/rules` | אמיתי | ב' | קובץ הכללים |
| `POST /api/compare` | **מדומה** | א' | `CompareResponse` |
| `POST /api/chat` | **מדומה** | ב' | `ConversationState` |
| `GET /api/conversations/{id}` | **מדומה** (בזיכרון) | ב' | `ConversationState` |
| `GET /api/rep/questions?status=open` | **מדומה** (בזיכרון) | א' | `list[RepQuestion]` |
| `POST /api/rep/questions/{id}/answer` | **מדומה** (בזיכרון) | א' | `RepQuestion` |

## מושגים מרכזיים

**`Tracked[T]`**: ערך ומקור. `source="missing"` אומר שהערך לא ידוע. המנוע מחזיר `status="partial"` ומוסיף את השדה ל-`missing`. הוא אף פעם לא ממלא ערך בעצמו.

**`OptionResult.status`**
- `complete`: יש את כל הנתונים, כל המספרים מחושבים.
- `partial`: חסר נתון (בדרך כלל השתתפות). נשלחה שאלה לנציג. `net` ו-`delta_net` הם `null`.
- `blocked`: אין זכאות. `eligibility.reason_text` מסביר למה.

**`trace`**: הקבלה של החישוב. ה-Number Guard בודק את הטקסט של הבוט מול השדות `amount` שבה.

**`waterfall`**: פירוק ההפרש. סכום ה-`amount` שווה בדיוק ל-`delta_net`. יש לזה בדיקה.

**עיגול**: השרת מחזיר ערכים בלי עיגול. הממשק מעגל לשקל ב-`design/format.js`.

## הזרימה כשחסר נתון

1. הסוכן מזהה שחסרה השתתפות לרכב X. הוא יוצר `RepQuestion` עם `field="participation:CAR-XX"`, וה-`status` של השיחה הופך ל-`waiting_for_rep`.
2. העובד רואה השוואה חלקית (`partial`) עם ההודעה "שאלתי את הנציג".
3. הנציג עונה. הערך נכנס לפרופיל עם `source="rep"` ו-`note` (תאריך תחולה), ומתבצע חישוב מחדש.
4. הממשק של העובד מושך את `GET /api/conversations/{id}` כל 2 שניות ורואה את ההשוואה המעודכנת.
