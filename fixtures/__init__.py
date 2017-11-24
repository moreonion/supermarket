from copy import deepcopy
from collections import defaultdict
import csv
import os.path
import re

import pycountry

from supermarket.model import (
    db,
    Brand,
    Criterion,
    CriterionCategory,
    CriterionImprovesHotspot,
    Hotspot,
    Ingredient,
    Label,
    LabelCountry,
    LabelMeetsCriterion,
    Origin,
    Product,
    Resource,
    Retailer,
)

criteria_code_pattern = re.compile('^\d\.\d\.\d$')


def import_example_data():
    db.drop_all()
    db.create_all()
    lang = 'en'  # assuming everything is English for now

    # Hotspots
    db.session.add_all([
        Hotspot(name={lang: 'Climate Risk'}),
        Hotspot(name={lang: 'Risk Deforestation / Biodiversity'}),
        Hotspot(name={lang: 'Pollution / Pesticides'}),
        Hotspot(name={lang: 'Risk of Landrights Violation'}),
        Hotspot(name={lang: 'Risk of Workers Right Violation'}),
        Hotspot(name={lang: 'Poverty Risk'}),
        Hotspot(name={lang: 'Transparency'}),
    ])
    db.session.commit()

    # Labels and general scoring
    labels = {}
    resources = {}
    # score_map = {
    #     'red': 1,
    #     'no evaluation*': 1,
    #     'red/yellow': 1,
    #     'red/yellow mix': 1,
    #     'green/yellow': 2,
    #     'yellow': 2,
    #     'green': 3,
    # }
    label_int = LabelCountry(code='*')
    label_at = LabelCountry(code='AT')
    label_de = LabelCountry(code='DE')
    label_countries_map = {
        'international': label_int,
        'Austria': label_at,
        'Germany': label_de
    }
    logo_map = {
        'GSCP': {lang: 'https://ucarecdn.com/3fcc6856-4df5-4c89-862d-8f749685b922/'},
        'Fairtrade Cacao': {lang: 'https://ucarecdn.com/d789afc3-34e8-44ba-b487-55bcce8d387e/'},
        'Fairtrade': {lang: 'https://ucarecdn.com/b3f8f378-54bf-420c-ab38-a71fbf5d6b91/'},
        'RSPO': {lang: 'https://ucarecdn.com/31666604-b624-46f5-8ab3-b977df957f82/'},
        'FSC': {lang: 'https://ucarecdn.com/8c12e2c7-c021-40a8-8cb1-d1446d8bd108/'},
        'SGF': {lang: 'https://ucarecdn.com/4fd8ed9b-c0e5-40fe-b0db-de05920352a9/'},
        'GRI': {lang: 'https://ucarecdn.com/5fc14fed-4472-42be-b4d2-230b1bdd396f/'},
        'Rainforest Alliance': {
            lang: 'https://ucarecdn.com/8111e8bb-2ce9-4d57-af34-272e20acb16c/'},
        'FLA': {lang: 'https://ucarecdn.com/61b47438-2ca1-4975-aaa6-b7bd8e3f1853/'},
        'Global Coffee Platform': {
            lang: 'https://ucarecdn.com/e1511730-18e1-4343-abe8-86474733e43f/'},
        'GLOBALG.A.P': {lang: 'https://ucarecdn.com/4ca37337-ac7f-4f5f-9bc5-a898e6129f74/'},
        'BEPI': {lang: 'https://ucarecdn.com/80ea63e2-2b2e-40b3-948d-5ff4d06c9a8b/'},
        'ETI': {lang: 'https://ucarecdn.com/67549bb3-cb42-43e3-b42f-f5172abaad2f/'},
        'UTZ Cacao': {
            lang: 'https://ucarecdn.com/f64d0875-3de2-4dff-a46e-ea0bc0d4bd31/'},  # same as UTZ
        'UTZ': {lang: 'https://ucarecdn.com/f64d0875-3de2-4dff-a46e-ea0bc0d4bd31/'},
        'MSC': {lang: 'https://ucarecdn.com/4fb9ce37-9c0e-437b-a124-fb4da09da29f/'},
        'FFL': {lang: 'https://ucarecdn.com/394fdb30-bf12-4b49-b4ff-6de88eac25bf/'},
        'SAI Platform': {lang: 'https://ucarecdn.com/4e5f6129-fe89-44e3-8ee0-b2dc232cd9a8/'},
        'EU organic': {lang: 'https://ucarecdn.com/3aff3937-0062-4c89-b224-08afe40388f3/'},
        'BSCI': {lang: 'https://ucarecdn.com/23e18353-9638-4d89-aee3-e9b2bf58be50/'},
        'SA 8000': {lang: 'https://ucarecdn.com/35951758-eb0f-452f-8cdf-23886a0cb1a3/'},
        'DLG': {lang: 'https://ucarecdn.com/24d486ca-eb04-4c42-bd4d-99a2a4a7573c/'},
        'ohne GEN': {lang: 'https://ucarecdn.com/63907583-054a-4744-840c-a1a696b39e0a/'},
        'Alnatura': {lang: 'https://ucarecdn.com/9e6e8fa1-a2e3-41e9-a492-960658f2f442/'},
        'AMA-Biozeichen (rot/weiß)': {
            lang: 'https://ucarecdn.com/f49cfe62-fc4f-4937-bf28-32a6642c0c16/'},
        'AMA-Gütesiegel': {lang: 'https://ucarecdn.com/4e533b0b-980f-40d9-a9ab-641349cf66d1/'},
        'Bio Austria': {lang: 'https://ucarecdn.com/689fac65-bb49-4b56-82a7-af58badf1616/'},
        'Bio vom Berg': {lang: 'https://ucarecdn.com/bbd4f2aa-de10-40c5-b37e-f8a3c7ae8ba7/'},
        'Demeter': {lang: 'https://ucarecdn.com/83684e89-d085-4e43-a683-b950486d5f43/'},
        'ECHT B!O': {lang: 'https://ucarecdn.com/31bef53d-34df-48bf-85b9-52f06f029a45/'},
        'Ja! Natürlich': {lang: 'https://ucarecdn.com/d2f791bb-255a-4106-8939-7b1e7e2b6f5e/'},
        'Natürlich für uns': {
            lang: 'https://ucarecdn.com/aad93ae5-cbf4-4199-82ef-25455acd5d26/'},
        'Natur aktiv': {
            lang: 'https://ucarecdn.com/a2c47e54-29fd-4fc7-ba84-56f667c21132/'},
        'Pro Planet Obst, Gemüse, Eier und Wein': {
            lang: 'https://ucarecdn.com/c7698312-4124-4a83-ba55-e05e6fc64e5f/'},
        'Pro Planet – weitere Produkte': {
            lang: 'https://ucarecdn.com/c7698312-4124-4a83-ba55-e05e6fc64e5f/'},
        'Spar Natur Pur': {lang: 'https://ucarecdn.com/5ea60468-9ad1-495a-bca4-1adc2a567c01/'},
        'Tierwohl verbessert': {
            lang: 'https://ucarecdn.com/5d6c22e2-85e6-4792-bb5f-a5b3acde3782/'},
        'Tierwohl kontrolliert': {
            lang: 'https://ucarecdn.com/27292a9d-6ac6-4e32-840f-2e6b1a698832/'},  # 2 ticks
        #   lang: 'https://ucarecdn.com/d5811b3c-45bb-4adc-8e11-8126ed799416/'},  # 3 ticks
        'Zurück zum Ursprung': {
            lang: 'https://ucarecdn.com/28e89765-a1e3-4fa3-9da3-194fae43a1da/'},
        'Blühendes Österreich': {
            lang: 'https://ucarecdn.com/b5fff13a-e94f-4eb6-9e39-26d687791304/'},
        'Ich bin Österreich': {lang: 'https://ucarecdn.com/3b99d4df-f783-46a5-b0c0-ca24f0500ff8/'},
        'Rapunzel': {lang: 'https://ucarecdn.com/d7a81ab1-e506-484d-965e-90fe07546d25/'},
        'GEPA': {lang: 'https://ucarecdn.com/61f427d9-a3ed-4336-9d40-e07efe9c940e/'}
    }
    missing_logos = []
    with open(os.path.dirname(__file__) + '/csvs/label-info.csv') as csv_file:
        reader = csv.reader(csv_file)
        next(reader)  # Skip the header line.
        for row in reader:
            name = row[0]
            applies_to, bto, country = row[1], row[4], row[6]
            description_en, description_de = row[7], row[8]
            # credibility, environment, social, animal_welfare = row[9], row[10], row[11], row[12]

            ltype = None
            if bto.strip() == 'BtoB':
                ltype = 'retailer'
            elif bto.strip() == 'BtoC':
                ltype = 'product'

            l = Label(
                type=ltype,
                name={'de': name},
                description={'de': description_de},
                # details=dict(score=dict(
                #     credibility=int(credibility),
                #     environment=int(environment),
                #     social=int(social),
                #     animal_welfare=int(animal_welfare)
                # ))
            )

            if name in logo_map:
                l.logo = logo_map[name]
            else:
                missing_logos.append(name)

            if description_en:
                # add English description
                description_dict = deepcopy(l.description)
                description_dict['en'] = description_en
                l.description = description_dict
                # assume name is the same in English if we don’t know better
                name_dict = deepcopy(l.name)
                name_dict['en'] = name
                if name == 'EU organic':
                    name_dict['de'] = 'EU Biosiegel'
                l.name = name_dict

            if country:
                for c in (c.strip() for c in country.split(';')):
                    l.countries.append(label_countries_map[c])

            if applies_to and applies_to != 'n.a.' and not applies_to.startswith('all'):
                for r in (r.strip().capitalize() for r in applies_to.split(',')):
                    if r not in resources:
                        resources[r] = Resource(name={lang: r})
                    l.resources.append(resources[r])

            labels[name] = l
            db.session.add(l)
    print("*** Imported labels ***\n'{}'\n".format("', '".join(list(labels.keys()))))
    if missing_logos:
        print("Missing logos for:\n'{}'\n".format("', '".join(missing_logos)))
    db.session.commit()

    # Criteria and label scores
    criteria = {}
    categories = []
    unknown_labels = set()
    with open(os.path.dirname(__file__) + '/csvs/criteria-labels.csv') as csv_file:
        reader = csv.reader(csv_file)
        label_codes = next(reader)[11:]
        for row in reader:
            # if row[11]:  # exclude from scoring
            #     continue
            (category_name, subcategory_name, criterion_name) = (row[1], row[3], row[5])
            if criterion_name == 'Consumer communication: label':
                continue  # criterion data in csv is incomplete
            criterion = Criterion.query.filter(
                Criterion.name[lang].astext == criterion_name).first()
            if criterion is None:
                subcategory = CriterionCategory.query.filter(
                    CriterionCategory.name[lang].astext == subcategory_name).first()
                if subcategory is None:
                    category = CriterionCategory.query.filter(
                        CriterionCategory.name[lang].astext == category_name).first()
                    if category is None:
                        category = CriterionCategory(name={lang: category_name})
                        db.session.add(category)
                        categories.append(category)
                    subcategory = CriterionCategory(
                        name={lang: subcategory_name}, category=category)
                    db.session.add(subcategory)
                criterion = Criterion(
                    name={lang: criterion_name},
                    category=subcategory,
                    # use English text for German questions as there is no translation provided
                    details={'en': {'question': row[6], 'measures': {}},
                             'de': {'question': row[6], 'measures': {}}}
                )
                db.session.add(criterion)
                criteria[row[4]] = criterion
            details = deepcopy(criterion.details)
            details['en']['measures'][int(row[10])] = row[8]  # English text
            details['de']['measures'][int(row[10])] = row[9]  # German text
            criterion.details = details
            db.session.add(criterion)

            for label_code, s in zip(label_codes, row[11:]):
                label_code = label_code.strip()
                if label_code not in labels:
                    unknown_labels.add(label_code)
                    continue
                if not s or int(s) <= 0:
                    continue
                db.session.add(LabelMeetsCriterion(
                    label=labels[label_code],
                    criterion=criterion,
                    score=s,
                    explanation={
                        'en': row[8],
                        'de': row[9]
                    }
                ))
    if unknown_labels:
        print("Couldn’t apply criteria scores to unknown labels:\n'{}'\n".format(
            "', '".join(unknown_labels)))
    db.session.commit()

    # calculate label scoring
    category_scores = {}
    for category in categories:
        max_score = 0
        label_scores = defaultdict(lambda: 0)
        # subcategory score
        for subcategory in category.subcategories:
            max_sub_score = 0
            label_sub_scores = defaultdict(lambda: 0)
            for criterion in subcategory.criteria:
                # get maximum criterion score
                points = criterion.details[lang]['measures'].keys()
                max_sub_score += max(map(int, points))
                # get criterion score per label
                for lmc in LabelMeetsCriterion.query.filter_by(criterion_id=criterion.id).all():
                    label_sub_scores[lmc.label] += int(lmc.score)
            # calculate score for subcategory
            for label, score in label_sub_scores.items():
                label_scores[label] += round(100*score/max_sub_score)
            # each subcategory has a max score of 100% for the overall score,
            if 'Co-Labeling' not in subcategory.name['en']:  # co-labeling doesn’t count
                max_score += 100
        # calculate overall score
        label_scores = {l: round(100*s/max_score) for l, s in label_scores.items()}
        category_scores[category.name['en'].replace(' ', '_').lower()] = label_scores

    # save score to label details
    for label in labels.values():
        score = {}
        for category, ls in category_scores.items():
            p = ls[label] if label in ls else 0
            # map to color (1: red, 2: yellow, 3: green)
            # TODO: move mapping to label guide (EvalCircle.vue), save percentages instead
            if p < 33:
                score[category] = 1
            elif p < 55:
                score[category] = 2
            else:
                score[category] = 3
        details_dict = deepcopy(label.details) or {}
        details_dict['score'] = score
        label.details = details_dict
        db.session.add(label)
    db.session.commit()

    # Criteria and Criteria-Hotspot mapping
    unknown_criteria = set()
    with open(os.path.dirname(__file__) + '/csvs/hotspot-criteria.csv') as csv_file:
        reader = csv.DictReader(csv_file)
        hotspots = Hotspot.query.all()
        for row in reader:
            if not row['ID'] in criteria:
                unknown_criteria.add(row['ID'])
                continue
            c = criteria[row['ID']]
            for h in hotspots:
                if row[h.name[lang]] and not CriterionImprovesHotspot.query.get((c.id, h.id)):
                    db.session.add(CriterionImprovesHotspot(criterion=c, hotspot=h))
            db.session.add(c)
    if unknown_criteria:
        print("Couldn’t map hotspots to unknown critera:\n'{}'\n".format(
            "', '".join(unknown_criteria)))
    db.session.commit()

    # Origins
    for c in pycountry.countries:
        name = c.common_name if hasattr(c, 'common_name') else c.name
        db.session.add(Origin(code=c.alpha_2, name={lang: name}))
    db.session.commit()

    for code, name in [
        ('18', 'Arctic Sea'),
        ('21', 'Atlantic, Northwest'),
        ('27', 'Atlantic, Northeast'),
        ('31', 'Atlantic, Western Central'),
        ('34', 'Atlantic, Eastern Central'),
        ('37', 'Mediterranean and Black Sea'),
        ('41', 'Atlantic, Southwest'),
        ('47', 'Atlantic, Southeast'),
        ('48', 'Atlantic, Antarctic'),
        ('51', 'Indian Ocean, Western'),
        ('57', 'Indian Ocean, Eastern'),
        ('58', 'Indian Ocean, Antarctic and Southern'),
        ('61', 'Pacific, Northwest'),
        ('67', 'Pacific, Northeast'),
        ('71', 'Pacific, Western Central'),
        ('77', 'Pacific, Eastern Central'),
        ('81', 'Pacific, Southwest'),
        ('87', 'Pacific, Southeast'),
        ('88', 'Pacific, Antarctic'),
    ]:
        db.session.add(Origin(code=code, name={lang: name}))
    db.session.commit()

    # Products - Brands - Retailers
    products = dict()
    retailers = dict()
    brands = dict()
    with open(os.path.dirname(__file__) + '/csvs/Data_1_Example_Product.csv') as csv_file:
        for row in csv.DictReader(csv_file):
            if row['Retailer'] not in retailers:
                retailers[row['Retailer']] = Retailer(name=row['Retailer'])
            if row['Brand'] and row['Brand'] not in brands:
                brands[row['Brand']] = Brand(
                    name=row['Brand'],
                    retailer=retailers[row['Retailer']],
                )
            p = Product(
                name={lang: row['Complete product Name']},
                gtin=row['Barcode Number (number below barcode)'],
            )
            if row['Brand']:
                p.brand = brands[row['Brand']]
            products[row['Product ID']] = p
            db.session.add(p)

    # Ingredients
    with open(os.path.dirname(__file__) + '/csvs/Data_2_Example_Ingredients.csv') as csv_file:
        next(csv_file)  # Skip header line.
        for row in csv.reader(csv_file):
            if not row[0] in products:
                print("Ingredient for unknown product: {}".format(row[0]))
                continue

            weight = 1
            for ingredient, percentage, origin in [
                    (row[i], row[i+1], row[i+2]) for i in range(4, len(row)-2, 3)]:
                if not ingredient:
                    continue
                i = Ingredient(
                    name={lang: ingredient},
                    product=products[row[0]],
                    weight=weight,
                )
                if percentage:
                    try:
                        p = float(percentage.strip(' %').replace(',', '.'))
                        if p < 1:
                            p = int(p * 100)
                        i.percentage = p
                    except ValueError:
                        pass  # Nothing number-like in there.
                db.session.add(i)
                weight += 1

    # Product labels
    with open(os.path.dirname(__file__) + '/csvs/Data_2_Example_Labels.csv') as csv_file:
        next(csv_file)  # Skip header line.
        for row in csv.reader(csv_file):
            if not row[0] in products:
                print("Label for unknown product: {}".format(row[0]))
                continue

            p = products[row[0]]
            plabels = []
            for label in row[5:]:
                if label:
                    if label.startswith('EU Biosiegel'):
                        label = 'EU organic'
                    if label.startswith('UTZ'):
                        label = 'UTZ'
                    label = label.replace('FAIRTRADE', 'Fairtrade')
                    label = label.replace('Roundtable on Sustainable Palm Oil (RSPO)', 'RSPO')
                    if label not in labels:
                        print("Unknown product label '{}'".format(label))
                        continue
                    plabels.append(labels[label])
            p.labels = plabels
    db.session.commit()
