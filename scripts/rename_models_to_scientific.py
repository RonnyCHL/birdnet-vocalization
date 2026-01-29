#!/usr/bin/env python3
"""
Rename vocalization models from Dutch common names to scientific names.

This makes the models work with any BirdNET-Pi language setting,
since scientific names are universal.

Usage:
    python rename_models_to_scientific.py --source /path/to/dutch/models --dest /path/to/scientific/models
"""

import argparse
import shutil
from pathlib import Path

# Mapping: Dutch name (lowercase, underscores) -> Scientific name
# Based on BirdNET-Pi labels and our trained models
DUTCH_TO_SCIENTIFIC = {
    'aalscholver': 'Phalacrocorax_carbo',
    'appelvink': 'Coccothraustes_coccothraustes',
    'baardman': 'Panurus_biarmicus',
    'barmsijs': 'Acanthis_flammea',  # Grote Barmsijs
    'beflijster': 'Turdus_torquatus',
    'bergeend': 'Tadorna_tadorna',
    'bijeneter': 'Merops_apiaster',
    'blauwborst': 'Luscinia_svecica',
    'blauwe_kiekendief': 'Circus_cyaneus',
    'blauwe_reiger': 'Ardea_cinerea',
    'boerenzwaluw': 'Hirundo_rustica',
    'bokje': 'Lymnocryptes_minimus',
    'bontbekplevier': 'Charadrius_hiaticula',
    'bonte_kraai': 'Corvus_cornix',
    'bonte_strandloper': 'Calidris_alpina',
    'bonte_vliegenvanger': 'Ficedula_hypoleuca',
    'boomklever': 'Sitta_europaea',
    'boomkruiper': 'Certhia_brachydactyla',
    'boomleeuwerik': 'Lullula_arborea',
    'boompieper': 'Anthus_trivialis',
    'boomvalk': 'Falco_subbuteo',
    'bosrietzanger': 'Acrocephalus_palustris',
    'bosruiter': 'Tringa_glareola',
    'bosuil': 'Strix_aluco',
    'braamsluiper': 'Curruca_curruca',
    'brandgans': 'Branta_leucopsis',
    'brilduiker': 'Bucephala_clangula',
    'bruine_kiekendief': 'Circus_aeruginosus',
    'buidelmees': 'Remiz_pendulinus',
    'buizerd': 'Buteo_buteo',
    'canadese_gans': 'Branta_canadensis',
    'cettis_zanger': 'Cettia_cetti',
    'citroenkanarie': 'Crithagra_citrinella',  # or Serinus citrinella
    'dodaars': 'Tachybaptus_ruficollis',
    'draaihals': 'Jynx_torquilla',
    'drieteenstrandloper': 'Calidris_alba',
    'dwergstern': 'Sternula_albifrons',
    'eider': 'Somateria_mollissima',
    'ekster': 'Pica_pica',
    'europese_kanarie': 'Serinus_serinus',
    'fazant': 'Phasianus_colchicus',
    'fitis': 'Phylloscopus_trochilus',
    'flamingo': 'Phoenicopterus_roseus',
    'fluiter': 'Phylloscopus_sibilatrix',
    'fuut': 'Podiceps_cristatus',
    'gaai': 'Garrulus_glandarius',
    'geelgors': 'Emberiza_citrinella',
    'gekraagde_roodstaart': 'Phoenicurus_phoenicurus',
    'gele_kwikstaart': 'Motacilla_flava',
    'gierzwaluw': 'Apus_apus',
    'goudhaantje': 'Regulus_regulus',
    'goudplevier': 'Pluvialis_apricaria',
    'goudvink': 'Pyrrhula_pyrrhula',
    'graszanger': 'Cisticola_juncidis',
    'grauwe_gans': 'Anser_anser',
    'grauwe_gors': 'Emberiza_calandra',
    'grauwe_kiekendief': 'Circus_pygargus',
    'grauwe_klauwier': 'Lanius_collurio',
    'grauwe_vliegenvanger': 'Muscicapa_striata',
    'groene_specht': 'Picus_viridis',
    'groenling': 'Chloris_chloris',
    'grote_bonte_specht': 'Dendrocopos_major',
    'grote_gele_kwikstaart': 'Motacilla_cinerea',
    'grote_lijster': 'Turdus_viscivorus',
    'grote_mantelmeeuw': 'Larus_marinus',
    'grote_stern': 'Thalasseus_sandvicensis',
    'grote_zilverreiger': 'Ardea_alba',
    'grutto': 'Limosa_limosa',
    'havik': 'Accipiter_gentilis',
    'heggenmus': 'Prunella_modularis',
    'holenduif': 'Columba_oenas',
    'houtduif': 'Columba_palumbus',
    'houtsnip': 'Scolopax_rusticola',
    'huismus': 'Passer_domesticus',
    'huiszwaluw': 'Delichon_urbicum',
    'ijsvogel': 'Alcedo_atthis',
    'kauw': 'Coloeus_monedula',
    'keep': 'Fringilla_montifringilla',
    'kemphaan': 'Calidris_pugnax',
    'kievit': 'Vanellus_vanellus',
    'klapekster': 'Lanius_excubitor',
    'kleine_barmsijs': 'Acanthis_cabaret',
    'kleine_bonte_specht': 'Dryobates_minor',
    'kleine_karekiet': 'Acrocephalus_scirpaceus',
    'kleine_mantelmeeuw': 'Larus_fuscus',
    'kleine_plevier': 'Charadrius_dubius',
    'kleine_zilverreiger': 'Egretta_garzetta',
    'kluut': 'Recurvirostra_avosetta',
    'kneu': 'Linaria_cannabina',
    'knobbelzwaan': 'Cygnus_olor',
    'koereiger': 'Bubulcus_ibis',
    'kokmeeuw': 'Chroicocephalus_ridibundus',
    'kolgans': 'Anser_albifrons',
    'koolmees': 'Parus_major',
    'koperwiek': 'Turdus_iliacus',
    'kortsnavelboomkruiper': 'Certhia_familiaris',
    'kraanvogel': 'Grus_grus',
    'kramsvogel': 'Turdus_pilaris',
    'krakeend': 'Mareca_strepera',
    'kruisbek': 'Loxia_curvirostra',
    'kuifeend': 'Aythya_fuligula',
    'kuifleeuwerik': 'Galerida_cristata',
    'kuifmees': 'Lophophanes_cristatus',
    'kwak': 'Nycticorax_nycticorax',
    'kwartel': 'Coturnix_coturnix',
    'kwartelkoning': 'Crex_crex',
    'lepelaar': 'Platalea_leucorodia',
    'matkop': 'Poecile_montanus',
    'meerkoet': 'Fulica_atra',
    'merel': 'Turdus_merula',
    'middelste_bonte_specht': 'Dendrocoptes_medius',
    'nachtegaal': 'Luscinia_megarhynchos',
    'nachtzwaluw': 'Caprimulgus_europaeus',
    'nijlgans': 'Alopochen_aegyptiaca',
    'noordse_stern': 'Sterna_paradisaea',
    'notenkraker': 'Nucifraga_caryocatactes',
    'oehoe': 'Bubo_bubo',
    'oeverloper': 'Actitis_hypoleucos',
    'oeverzwaluw': 'Riparia_riparia',
    'ooievaar': 'Ciconia_ciconia',
    'orpheusspotvogel': 'Hippolais_polyglotta',
    'ortolaan': 'Emberiza_hortulana',
    'paapje': 'Saxicola_rubetra',
    'patrijs': 'Perdix_perdix',
    'pestvogel': 'Bombycilla_garrulus',
    'pijlstaart': 'Anas_acuta',
    'pimpelmees': 'Cyanistes_caeruleus',
    'porseleinhoen': 'Porzana_porzana',
    'putter': 'Carduelis_carduelis',
    'raaf': 'Corvus_corax',
    'ransuil': 'Asio_otus',
    'regenwulp': 'Numenius_phaeopus',
    'rietgors': 'Emberiza_schoeniclus',
    'rietzanger': 'Acrocephalus_schoenobaenus',
    'ringmus': 'Passer_montanus',
    'roek': 'Corvus_frugilegus',
    'roodborst': 'Erithacus_rubecula',
    'roodhalsfuut': 'Podiceps_grisegena',
    'roodkeelduiker': 'Gavia_stellata',
    'roodstuitzwaluw': 'Cecropis_daurica',
    'scholekster': 'Haematopus_ostralegus',
    'sijs': 'Spinus_spinus',
    'slobeend': 'Spatula_clypeata',
    'smient': 'Mareca_penelope',
    'sneeuwgors': 'Plectrophenax_nivalis',
    'snor': 'Locustella_luscinioides',
    'specht': 'Dendrocopos_major',  # Grote bonte specht (default)
    'sperwer': 'Accipiter_nisus',
    'spotvogel': 'Hippolais_icterina',
    'spreeuw': 'Sturnus_vulgaris',
    'sprinkhaanzanger': 'Locustella_naevia',
    'staartmees': 'Aegithalos_caudatus',
    'steenloper': 'Arenaria_interpres',
    'steenuil': 'Athene_noctua',
    'strandplevier': 'Charadrius_alexandrinus',
    'tafeleend': 'Aythya_ferina',
    'tapuit': 'Oenanthe_oenanthe',
    'tjiftjaf': 'Phylloscopus_collybita',
    'torenvalk': 'Falco_tinnunculus',
    'tuinfluiter': 'Sylvia_borin',
    'tureluur': 'Tringa_totanus',
    'turkse_tortel': 'Streptopelia_decaocto',
    'velduil': 'Asio_flammeus',
    'veldleeuwerik': 'Alauda_arvensis',
    'vink': 'Fringilla_coelebs',
    'visarend': 'Pandion_haliaetus',
    'visdief': 'Sterna_hirundo',
    'vuurgoudhaan': 'Regulus_ignicapilla',
    'waterhoen': 'Gallinula_chloropus',
    'waterpieper': 'Anthus_spinoletta',
    'waterral': 'Rallus_aquaticus',
    'watersnip': 'Gallinago_gallinago',
    'wespendief': 'Pernis_apivorus',
    'wielewaal': 'Oriolus_oriolus',
    'wilde_eend': 'Anas_platyrhynchos',
    'wilde_zwaan': 'Cygnus_cygnus',
    'winterkoning': 'Troglodytes_troglodytes',
    'wintertaling': 'Anas_crecca',
    'witgatje': 'Tringa_ochropus',
    'witte_kwikstaart': 'Motacilla_alba',
    'woudaap': 'Ixobrychus_minutus',
    'wulp': 'Numenius_arquata',
    'zanglijster': 'Turdus_philomelos',
    'zeearend': 'Haliaeetus_albicilla',
    'zilvermeeuw': 'Larus_argentatus',
    'zilverplevier': 'Pluvialis_squatarola',
    'zomertaling': 'Spatula_querquedula',
    'zomertortel': 'Streptopelia_turtur',
    'zwarte_kraai': 'Corvus_corone',
    'zwarte_mees': 'Periparus_ater',
    'zwarte_roodstaart': 'Phoenicurus_ochruros',
    'zwarte_ruiter': 'Tringa_erythropus',
    'zwarte_specht': 'Dryocopus_martius',
    'zwarte_stern': 'Chlidonias_niger',
    'zwarte_wouw': 'Milvus_migrans',
    'zwarte_zwaan': 'Cygnus_atratus',
    'zwartkop': 'Sylvia_atricapilla',
    'zwartkopmeeuw': 'Ichthyaetus_melanocephalus',
    # Additional mappings for missing species
    'glanskop': 'Poecile_palustris',
    'goudhaan': 'Regulus_regulus',  # Goudhaantje
    'grasmus': 'Curruca_communis',
    'graspieper': 'Anthus_pratensis',
    'groenpootruiter': 'Tringa_nebularia',
    'grote_canadese_gans': 'Branta_canadensis',  # Same as canadese_gans
    'grote_karekiet': 'Acrocephalus_arundinaceus',
    'grote_zaagbek': 'Mergus_merganser',
    'haakbek': 'Pinicola_enucleator',
    'hop': 'Upupa_epops',
    'kanoetstrandloper': 'Calidris_canutus',
    'kerkuil': 'Tyto_alba',
    'kleine_rietgans': 'Anser_brachyrhynchus',
    'kleine_strandloper': 'Calidris_minuta',
    'kleine_zwaan': 'Cygnus_columbianus',
    'koekoek': 'Cuculus_canorus',
    'mandarijneend': 'Aix_galericulata',
    'middelste_zaagbek': 'Mergus_serrator',
    'nonnetje': 'Mergellus_albellus',
    'rode_wouw': 'Milvus_milvus',
    'roerdomp': 'Botaurus_stellaris',
    'roodborsttapuit': 'Saxicola_rubicola',
    'rosse_grutto': 'Limosa_lapponica',
    'rotsduif': 'Columba_livia',
    'scharrelaar': 'Coracias_garrulus',
    'slechtvalk': 'Falco_peregrinus',
    'smelleken': 'Falco_columbarius',
    'stadsduif': 'Columba_livia',  # Same as rotsduif (feral)
    'stormmeeuw': 'Larus_canus',
    'taigaboomkruiper': 'Certhia_familiaris',
    'toendrarietgans': 'Anser_serrirostris',
    'witgat': 'Tringa_ochropus',  # Already have witgatje
}


def rename_models(source_dir: Path, dest_dir: Path, dry_run: bool = False):
    """Rename model files from Dutch to scientific names."""
    source_dir = Path(source_dir)
    dest_dir = Path(dest_dir)

    if not source_dir.exists():
        print(f"Error: Source directory not found: {source_dir}")
        return

    if not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)

    renamed = 0
    skipped = 0
    not_found = []

    for model_file in sorted(source_dir.glob("*.pt")):
        # Extract Dutch name from filename
        # Format: dutch_name_cnn_2025_ultimate.pt
        name = model_file.stem

        # Skip non-species models
        if 'distance_quality' in name:
            print(f"  Skipping non-species model: {model_file.name}")
            skipped += 1
            continue

        # Extract species part
        if '_cnn_' in name:
            dutch_name = name.split('_cnn_')[0]
        else:
            dutch_name = name

        # Look up scientific name
        scientific = DUTCH_TO_SCIENTIFIC.get(dutch_name)

        if not scientific:
            not_found.append(dutch_name)
            skipped += 1
            continue

        # Create new filename
        new_name = f"{scientific}.pt"
        dest_path = dest_dir / new_name

        if dry_run:
            print(f"  {model_file.name} -> {new_name}")
        else:
            shutil.copy2(model_file, dest_path)
            print(f"  Copied: {model_file.name} -> {new_name}")

        renamed += 1

    print(f"\nSummary:")
    print(f"  Renamed: {renamed}")
    print(f"  Skipped: {skipped}")

    if not_found:
        print(f"\n  Missing mappings ({len(not_found)}):")
        for name in sorted(not_found):
            print(f"    - {name}")


def main():
    parser = argparse.ArgumentParser(description="Rename vocalization models to scientific names")
    parser.add_argument("--source", type=Path, required=True, help="Source directory with Dutch-named models")
    parser.add_argument("--dest", type=Path, required=True, help="Destination directory for scientific-named models")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without copying")

    args = parser.parse_args()

    print(f"Renaming models from Dutch to scientific names")
    print(f"  Source: {args.source}")
    print(f"  Dest:   {args.dest}")
    print(f"  Dry run: {args.dry_run}")
    print()

    rename_models(args.source, args.dest, args.dry_run)


if __name__ == "__main__":
    main()
