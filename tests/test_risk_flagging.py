#!/usr/bin/env python3
"""
Test Risk Flagging Model
Tests the moderation system against labeled risk/non-risk phrases
"""

import sys
import os
import csv
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from moderation import moderate_content, categorize_flagged_content
import openai
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def test_risk_flagging(csv_file):
    """Test risk flagging on the dataset"""

    print("="*70)
    print("MINDMITRA RISK FLAGGING TEST")
    print("="*70)
    print(f"Test Dataset: {csv_file}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    # Read test dataset
    test_cases = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            test_cases.append({
                'id': row['ID'],
                'text': row['Text'],
                'true_label': row['Label']
            })

    print(f"\n📊 Total test cases: {len(test_cases)}")

    # Split by language
    english_risk = [t for t in test_cases if t['id'].startswith('R-') and int(t['id'].split('-')[1]) <= 100]
    hinglish_risk = [t for t in test_cases if t['id'].startswith('R-') and int(t['id'].split('-')[1]) > 100]
    english_nonrisk = [t for t in test_cases if t['id'].startswith('NR-') and int(t['id'].split('-')[1]) <= 100]
    hinglish_nonrisk = [t for t in test_cases if t['id'].startswith('NR-') and int(t['id'].split('-')[1]) > 100]

    print(f"   - English Risk: {len(english_risk)}")
    print(f"   - Hinglish Risk: {len(hinglish_risk)}")
    print(f"   - English Non-Risk: {len(english_nonrisk)}")
    print(f"   - Hinglish Non-Risk: {len(hinglish_nonrisk)}")

    # Run tests
    print("\n🔍 Testing messages...")
    print("-"*70)

    results = []
    for i, test_case in enumerate(test_cases, 1):
        # Call moderation API
        is_safe, moderation_result = moderate_content(test_case['text'], openai_client)

        # Determine if flagged
        flagged = not is_safe

        # Get category if flagged
        category = None
        if flagged:
            category = categorize_flagged_content(test_case['text'], openai_client)

        # Store result
        result = {
            'id': test_case['id'],
            'text': test_case['text'],
            'true_label': test_case['true_label'],
            'flagged': flagged,
            'category': category,
            'correct': (test_case['true_label'] == 'Risk' and flagged) or
                      (test_case['true_label'] == 'Non-Risk' and not flagged)
        }
        results.append(result)

        # Progress indicator
        if i % 10 == 0:
            print(f"   Processed: {i}/{len(test_cases)}...")

    print(f"   Processed: {len(test_cases)}/{len(test_cases)} ✅")

    # Calculate metrics
    print("\n" + "="*70)
    print("📈 RESULTS")
    print("="*70)

    # Overall metrics
    true_positives = sum(1 for r in results if r['true_label'] == 'Risk' and r['flagged'])
    true_negatives = sum(1 for r in results if r['true_label'] == 'Non-Risk' and not r['flagged'])
    false_positives = sum(1 for r in results if r['true_label'] == 'Non-Risk' and r['flagged'])
    false_negatives = sum(1 for r in results if r['true_label'] == 'Risk' and not r['flagged'])

    total = len(results)
    accuracy = (true_positives + true_negatives) / total * 100
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    print("\n🎯 OVERALL PERFORMANCE:")
    print(f"   Accuracy:  {accuracy:.2f}%")
    print(f"   Precision: {precision:.2f}")
    print(f"   Recall:    {recall:.2f}")
    print(f"   F1 Score:  {f1_score:.2f}")

    print("\n📊 CONFUSION MATRIX:")
    print(f"   True Positives  (Correctly flagged risk):     {true_positives}")
    print(f"   True Negatives  (Correctly ignored safe):     {true_negatives}")
    print(f"   False Positives (Incorrectly flagged safe):   {false_positives}")
    print(f"   False Negatives (Missed risk - CRITICAL!):    {false_negatives}")

    # Breakdown by language
    english_results = [r for r in results if int(r['id'].split('-')[1]) <= 100]
    hinglish_results = [r for r in results if int(r['id'].split('-')[1]) > 100]

    print("\n📝 ENGLISH vs HINGLISH:")

    # English
    eng_tp = sum(1 for r in english_results if r['true_label'] == 'Risk' and r['flagged'])
    eng_tn = sum(1 for r in english_results if r['true_label'] == 'Non-Risk' and not r['flagged'])
    eng_fp = sum(1 for r in english_results if r['true_label'] == 'Non-Risk' and r['flagged'])
    eng_fn = sum(1 for r in english_results if r['true_label'] == 'Risk' and not r['flagged'])
    eng_accuracy = (eng_tp + eng_tn) / len(english_results) * 100

    print(f"\n   English (1-100):")
    print(f"      Accuracy: {eng_accuracy:.2f}%")
    print(f"      TP: {eng_tp}  TN: {eng_tn}  FP: {eng_fp}  FN: {eng_fn}")

    # Hinglish
    hin_tp = sum(1 for r in hinglish_results if r['true_label'] == 'Risk' and r['flagged'])
    hin_tn = sum(1 for r in hinglish_results if r['true_label'] == 'Non-Risk' and not r['flagged'])
    hin_fp = sum(1 for r in hinglish_results if r['true_label'] == 'Non-Risk' and r['flagged'])
    hin_fn = sum(1 for r in hinglish_results if r['true_label'] == 'Risk' and not r['flagged'])
    hin_accuracy = (hin_tp + hin_tn) / len(hinglish_results) * 100

    print(f"\n   Hinglish (101-200):")
    print(f"      Accuracy: {hin_accuracy:.2f}%")
    print(f"      TP: {hin_tp}  TN: {hin_tn}  FP: {hin_fp}  FN: {hin_fn}")

    # Category breakdown
    if true_positives > 0:
        print("\n🏷️  RISK CATEGORIES (for flagged messages):")
        categories = {}
        for r in results:
            if r['flagged'] and r['category']:
                categories[r['category']] = categories.get(r['category'], 0) + 1

        for cat, count in sorted(categories.items()):
            cat_names = {
                'SI': 'Suicidal Ideation',
                'SH': 'Self-Harm',
                'HI': 'Harm to Others',
                'EA': 'Emotional Abuse'
            }
            print(f"      {cat} ({cat_names.get(cat, 'Unknown')}): {count}")

    # Critical errors (False Negatives)
    if false_negatives > 0:
        print(f"\n⚠️  CRITICAL: {false_negatives} RISK MESSAGES WERE MISSED!")
        print("   These phrases should be flagged but weren't:")
        for r in results:
            if r['true_label'] == 'Risk' and not r['flagged']:
                print(f"      [{r['id']}] {r['text'][:60]}...")

    # Save detailed results
    output_file = os.path.join(
        os.path.dirname(__file__),
        f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'text', 'true_label', 'flagged', 'category', 'correct'])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n💾 Detailed results saved to: {output_file}")
    print("="*70)

if __name__ == "__main__":
    csv_file = os.path.join(os.path.dirname(__file__), 'mindmitra_risk_test_dataset.csv')

    if not os.path.exists(csv_file):
        print(f"❌ Error: Test dataset not found: {csv_file}")
        sys.exit(1)

    test_risk_flagging(csv_file)
