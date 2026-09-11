import { Card } from "@/components/ui/Card";
import { IconRemote } from "@/components/icons";

const OUTILS = [
  {
    titre: "Chrome Remote Desktop",
    description: "Simple et rapide, nécessite le navigateur Chrome.",
    lien: "https://remotedesktop.google.com/support",
    libelleLien: "Ouvrir Chrome Remote Desktop",
  },
  {
    titre: "TeamViewer QuickSupport",
    description: "Aucune installation requise, fonctionne sur tout ordinateur.",
    lien: "https://www.teamviewer.com/fr/solutions/use-cases/quicksupport/",
    libelleLien: "Ouvrir TeamViewer QuickSupport",
  },
];

export default function RemotePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Prise en main à distance</h1>
        <p className="mt-1 text-slate-500">
          Pour une intervention à distance, ouvrez l&apos;un des outils ci-dessous et communiquez le code affiché à
          l&apos;écran par téléphone.
        </p>
      </div>

      <div className="grid gap-5 sm:grid-cols-2">
        {OUTILS.map((outil) => (
          <Card key={outil.titre} className="flex h-full flex-col">
            <span className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-brand-accent/15 text-brand-accent">
              <IconRemote width={22} height={22} />
            </span>
            <h2 className="font-bold text-slate-800">{outil.titre}</h2>
            <p className="mt-1 text-sm text-slate-500">{outil.description}</p>
            <a
              href={outil.lien}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-block text-sm font-semibold text-brand hover:underline"
            >
              {outil.libelleLien} →
            </a>
          </Card>
        ))}
      </div>
    </div>
  );
}
