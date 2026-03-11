import { ResearchNotebookScreen } from "@/components/ResearchNotebookScreen";
import { getNoteSynthesis, getResearchNotes, getResearchThemes, getResearchTheses } from "@/lib/api";

export default async function ResearchPage() {
  const defaultSymbol = "AAPL";

  const [notes, theses, themes, synthesis] = await Promise.all([
    getResearchNotes({ symbol: defaultSymbol, limit: 150 }),
    getResearchTheses(defaultSymbol),
    getResearchThemes(),
    getNoteSynthesis({ symbol: defaultSymbol })
  ]);

  return (
    <ResearchNotebookScreen
      initialNotes={notes}
      initialTheses={theses}
      initialThemes={themes}
      initialSynthesis={synthesis}
    />
  );
}
