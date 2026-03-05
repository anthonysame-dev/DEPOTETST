"""
Chiffre d'affaires de février 2026 — Odoo st.digital
Requête sur account.move (factures clients validées).
"""

from odoo_connection import main, execute

ANNEE   = 2026
MOIS    = 2
DATE_DU = f"{ANNEE}-{MOIS:02d}-01"
DATE_AU = f"{ANNEE}-{MOIS:02d}-28"   # février 2026 = 28 jours


def chiffre_affaires_fevrier():
    uid, db, models, api_key = main()

    # ── Factures clients validées en février ──────────────────────────────────
    domaine = [
        ["move_type",    "in",  ["out_invoice", "out_refund"]],
        ["state",        "=",   "posted"],
        ["invoice_date", ">=",  DATE_DU],
        ["invoice_date", "<=",  DATE_AU],
    ]

    factures = execute(
        models, db, uid, api_key,
        "account.move", "search_read",
        domaine,
        fields=["name", "partner_id", "invoice_date", "amount_untaxed",
                "amount_tax", "amount_total", "move_type", "currency_id"],
        order="invoice_date asc",
    )

    # ── Calcul des totaux ─────────────────────────────────────────────────────
    total_ht  = sum(f["amount_untaxed"] for f in factures if f["move_type"] == "out_invoice")
    total_tva = sum(f["amount_tax"]     for f in factures if f["move_type"] == "out_invoice")
    total_ttc = sum(f["amount_total"]   for f in factures if f["move_type"] == "out_invoice")
    avoirs_ht = sum(f["amount_untaxed"] for f in factures if f["move_type"] == "out_refund")
    net_ht    = total_ht - avoirs_ht

    devise = factures[0]["currency_id"][1] if factures else "EUR"

    # ── Affichage ─────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  CHIFFRE D'AFFAIRES — FÉVRIER {ANNEE}")
    print(f"{'='*60}")
    print(f"  Nombre de factures    : {sum(1 for f in factures if f['move_type']=='out_invoice')}")
    print(f"  Nombre d'avoirs       : {sum(1 for f in factures if f['move_type']=='out_refund')}")
    print(f"{'-'*60}")
    print(f"  CA brut HT            : {total_ht:>15,.2f} {devise}")
    print(f"  TVA                   : {total_tva:>15,.2f} {devise}")
    print(f"  CA brut TTC           : {total_ttc:>15,.2f} {devise}")
    print(f"  Avoirs HT             : {avoirs_ht:>15,.2f} {devise}")
    print(f"{'='*60}")
    print(f"  CA NET HT (avoirs déduits) : {net_ht:>12,.2f} {devise}")
    print(f"{'='*60}\n")

    # ── Détail par facture ────────────────────────────────────────────────────
    if factures:
        print(f"  {'Date':<12} {'Facture':<20} {'Client':<30} {'HT':>12}  {'TTC':>12}")
        print(f"  {'-'*90}")
        for f in factures:
            signe = "-" if f["move_type"] == "out_refund" else " "
            client = f["partner_id"][1] if f["partner_id"] else "—"
            print(
                f"  {f['invoice_date']:<12} {f['name']:<20} {client[:30]:<30} "
                f"{signe}{f['amount_untaxed']:>11,.2f}  {signe}{f['amount_total']:>11,.2f}"
            )

    return net_ht, devise


if __name__ == "__main__":
    chiffre_affaires_fevrier()
