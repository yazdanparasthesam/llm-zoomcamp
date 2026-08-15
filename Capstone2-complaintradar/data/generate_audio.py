"""Regenerate multimodal CFPB audio briefings with gTTS (optional; MP3s are committed)."""

from pathlib import Path

from gtts import gTTS

OUT = Path(__file__).resolve().parent / "audio"

BRIEFS = {
    "wells_fargo_briefing.mp3": (
        "ComplaintRadar audio briefing. Wells Fargo. This is a summary of public C F P B consumer narratives, "
        "not a legal finding and not a nationwide statistic. "
        "Checking customers repeatedly describe stacked overdraft and low-balance fees after pending deposits are held, "
        "and say agents refused fee reversals. Mortgage narratives mention payment-process trouble, escrow disputes, "
        "and servicing complaints. Use these themes to prioritize ops review. Always open the cited complaint I Ds in ComplaintRadar."
    ),
    "credit_bureau_briefing.mp3": (
        "ComplaintRadar audio briefing. Equifax, Experian, and TransUnion. "
        "Public C F P B narratives concentrate on incorrect information, mixed files, identity theft, "
        "and unauthorized hard inquiries. Consumers describe accounts they say were opened without their knowledge, "
        "and investigations they believe were incomplete. These are individual consented stories. "
        "Open the cited C F P B document I Ds before any compliance action."
    ),
    "student_loan_card_briefing.mp3": (
        "ComplaintRadar audio briefing. Navient student loans, Navy Federal auto loans, and Goldman Sachs Apple Card. "
        "Student-loan narratives mention servicer payment handling and forbearance confusion. "
        "Auto-loan stories include repossession and payment disputes. "
        "Card narratives include billing errors and unexpected account closures. "
        "This briefing is consumer voice only. It is not legal advice. Verify every claim against the original complaint text."
    ),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, text in BRIEFS.items():
        path = OUT / name
        gTTS(text=text, lang="en", slow=False).save(str(path))
        print(f"wrote {path} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
