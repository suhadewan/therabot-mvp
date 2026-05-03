#!/usr/bin/env python3
"""
Complete Risk Detection System Test
Tests BOTH keyword detection AND OpenAI moderation (the full workflow)
"""

import sys
import os
import csv
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from moderation import moderate_content, categorize_flagged_content, assess_mental_health_risk
from crisis_detection import detect_crisis_keywords
import openai
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def test_complete_risk_detection(csv_file):
    """Test the COMPLETE risk detection workflow"""

    print("="*70)
    print("COMPLETE RISK DETECTION SYSTEM TEST")
    print("Testing: Keyword Detection + Generic Moderation + Mental Health AI")
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

    # Run tests
    print("\n🔍 Testing messages through COMPLETE workflow...")
    print("-"*70)

    results = []
    for i, test_case in enumerate(test_cases, 1):
        # LEVEL 1: Keyword Detection (immediate crisis response)
        is_crisis_keyword, crisis_response = detect_crisis_keywords(test_case['text'])

        # LEVEL 2A: Generic Moderation (OpenAI Moderation API)
        is_safe, moderation_result = moderate_content(test_case['text'], openai_client)
        flagged_by_moderation = not is_safe

        # LEVEL 2B: Mental Health Risk Assessment (Dedicated GPT-4o-mini prompt)
        flagged_by_mh_ai, mh_category, mh_confidence = assess_mental_health_risk(test_case['text'], openai_client)

        # Get category from whichever method flagged it
        category = None
        if flagged_by_mh_ai:
            category = mh_category
        elif flagged_by_moderation:
            category = categorize_flagged_content(test_case['text'], openai_client)

        # COMBINED RESULT: Flagged if ANY method caught it
        flagged_overall = is_crisis_keyword or flagged_by_moderation or flagged_by_mh_ai

        # Determine which method(s) caught it
        detection_method = []
        if is_crisis_keyword:
            detection_method.append("Keyword")
        if flagged_by_moderation:
            detection_method.append("Moderation")
        if flagged_by_mh_ai:
            detection_method.append("MH-AI")

        detection_method_str = " + ".join(detection_method) if detection_method else "None"

        # Store result
        result = {
            'id': test_case['id'],
            'text': test_case['text'],
            'true_label': test_case['true_label'],
            'flagged_overall': flagged_overall,
            'flagged_by_keywords': is_crisis_keyword,
            'flagged_by_moderation': flagged_by_moderation,
            'flagged_by_mh_ai': flagged_by_mh_ai,
            'mh_confidence': mh_confidence,
            'detection_method': detection_method_str,
            'category': category,
            'correct': (test_case['true_label'] == 'Risk' and flagged_overall) or
                      (test_case['true_label'] == 'Non-Risk' and not flagged_overall)
        }
        results.append(result)

        # Progress indicator
        if i % 10 == 0:
            print(f"   Processed: {i}/{len(test_cases)}...")

    print(f"   Processed: {len(test_cases)}/{len(test_cases)} ✅")

    # Calculate metrics
    print("\n" + "="*70)
    print("📈 RESULTS - COMBINED DETECTION SYSTEM")
    print("="*70)

    # Overall metrics
    true_positives = sum(1 for r in results if r['true_label'] == 'Risk' and r['flagged_overall'])
    true_negatives = sum(1 for r in results if r['true_label'] == 'Non-Risk' and not r['flagged_overall'])
    false_positives = sum(1 for r in results if r['true_label'] == 'Non-Risk' and r['flagged_overall'])
    false_negatives = sum(1 for r in results if r['true_label'] == 'Risk' and not r['flagged_overall'])

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
    print(f"   True Positives  (Risk correctly flagged):      {true_positives}")
    print(f"   True Negatives  (Non-risk correctly ignored):  {true_negatives}")
    print(f"   False Positives (Non-risk incorrectly flagged): {false_positives}")
    print(f"   False Negatives (Risk MISSED - CRITICAL!):     {false_negatives}")

    # Detection method breakdown
    keyword_only = sum(1 for r in results if r['flagged_by_keywords'] and not r['flagged_by_moderation'] and not r['flagged_by_mh_ai'])
    moderation_only = sum(1 for r in results if r['flagged_by_moderation'] and not r['flagged_by_keywords'] and not r['flagged_by_mh_ai'])
    mh_ai_only = sum(1 for r in results if r['flagged_by_mh_ai'] and not r['flagged_by_keywords'] and not r['flagged_by_moderation'])
    multiple_methods = sum(1 for r in results if (r['flagged_by_keywords'] + r['flagged_by_moderation'] + r['flagged_by_mh_ai']) > 1)
    total_flagged = sum(1 for r in results if r['flagged_overall'])

    print("\n🔍 DETECTION METHOD BREAKDOWN:")
    print(f"   Total Flagged:                {total_flagged}")
    print(f"   Keyword Detection Only:       {keyword_only}")
    print(f"   Generic Moderation Only:      {moderation_only}")
    print(f"   Mental Health AI Only:        {mh_ai_only}")
    print(f"   Multiple Methods (overlap):   {multiple_methods}")

    # Individual method performance
    keyword_tp = sum(1 for r in results if r['true_label'] == 'Risk' and r['flagged_by_keywords'])
    keyword_fp = sum(1 for r in results if r['true_label'] == 'Non-Risk' and r['flagged_by_keywords'])
    keyword_fn = sum(1 for r in results if r['true_label'] == 'Risk' and not r['flagged_by_keywords'])

    moderation_tp = sum(1 for r in results if r['true_label'] == 'Risk' and r['flagged_by_moderation'])
    moderation_fp = sum(1 for r in results if r['true_label'] == 'Non-Risk' and r['flagged_by_moderation'])
    moderation_fn = sum(1 for r in results if r['true_label'] == 'Risk' and not r['flagged_by_moderation'])

    mh_ai_tp = sum(1 for r in results if r['true_label'] == 'Risk' and r['flagged_by_mh_ai'])
    mh_ai_fp = sum(1 for r in results if r['true_label'] == 'Non-Risk' and r['flagged_by_mh_ai'])
    mh_ai_fn = sum(1 for r in results if r['true_label'] == 'Risk' and not r['flagged_by_mh_ai'])

    keyword_precision = keyword_tp / (keyword_tp + keyword_fp) if (keyword_tp + keyword_fp) > 0 else 0
    keyword_recall = keyword_tp / (keyword_tp + keyword_fn) if (keyword_tp + keyword_fn) > 0 else 0

    moderation_precision = moderation_tp / (moderation_tp + moderation_fp) if (moderation_tp + moderation_fp) > 0 else 0
    moderation_recall = moderation_tp / (moderation_tp + moderation_fn) if (moderation_tp + moderation_fn) > 0 else 0

    mh_ai_precision = mh_ai_tp / (mh_ai_tp + mh_ai_fp) if (mh_ai_tp + mh_ai_fp) > 0 else 0
    mh_ai_recall = mh_ai_tp / (mh_ai_tp + mh_ai_fn) if (mh_ai_tp + mh_ai_fn) > 0 else 0

    print("\n📊 INDIVIDUAL METHOD PERFORMANCE:")
    print(f"\n   Keyword Detection:")
    print(f"      Precision: {keyword_precision:.2f}  |  Recall: {keyword_recall:.2f}")
    print(f"      TP: {keyword_tp}  FP: {keyword_fp}  FN: {keyword_fn}")

    print(f"\n   Generic OpenAI Moderation:")
    print(f"      Precision: {moderation_precision:.2f}  |  Recall: {moderation_recall:.2f}")
    print(f"      TP: {moderation_tp}  FP: {moderation_fp}  FN: {moderation_fn}")

    print(f"\n   Mental Health AI (NEW):")
    print(f"      Precision: {mh_ai_precision:.2f}  |  Recall: {mh_ai_recall:.2f}")
    print(f"      TP: {mh_ai_tp}  FP: {mh_ai_fp}  FN: {mh_ai_fn}")

    # Calculate average confidence for MH-AI detections
    mh_ai_confidences = [r['mh_confidence'] for r in results if r['flagged_by_mh_ai']]
    avg_confidence = sum(mh_ai_confidences) / len(mh_ai_confidences) if mh_ai_confidences else 0
    print(f"      Average Confidence: {avg_confidence:.2f}")

    # Breakdown by language
    english_results = [r for r in results if int(r['id'].split('-')[1]) <= 100]
    hinglish_results = [r for r in results if int(r['id'].split('-')[1]) > 100]

    print("\n📝 ENGLISH vs HINGLISH:")

    # English
    eng_tp = sum(1 for r in english_results if r['true_label'] == 'Risk' and r['flagged_overall'])
    eng_tn = sum(1 for r in english_results if r['true_label'] == 'Non-Risk' and not r['flagged_overall'])
    eng_fp = sum(1 for r in english_results if r['true_label'] == 'Non-Risk' and r['flagged_overall'])
    eng_fn = sum(1 for r in english_results if r['true_label'] == 'Risk' and not r['flagged_overall'])
    eng_accuracy = (eng_tp + eng_tn) / len(english_results) * 100

    print(f"\n   English (1-100):")
    print(f"      Accuracy: {eng_accuracy:.2f}%")
    print(f"      TP: {eng_tp}  TN: {eng_tn}  FP: {eng_fp}  FN: {eng_fn}")

    # Hinglish
    hin_tp = sum(1 for r in hinglish_results if r['true_label'] == 'Risk' and r['flagged_overall'])
    hin_tn = sum(1 for r in hinglish_results if r['true_label'] == 'Non-Risk' and not r['flagged_overall'])
    hin_fp = sum(1 for r in hinglish_results if r['true_label'] == 'Non-Risk' and r['flagged_overall'])
    hin_fn = sum(1 for r in hinglish_results if r['true_label'] == 'Risk' and not r['flagged_overall'])
    hin_accuracy = (hin_tp + hin_tn) / len(hinglish_results) * 100

    print(f"\n   Hinglish (101-200):")
    print(f"      Accuracy: {hin_accuracy:.2f}%")
    print(f"      TP: {hin_tp}  TN: {hin_tn}  FP: {hin_fp}  FN: {hin_fn}")

    # Category breakdown
    if moderation_tp > 0:
        print("\n🏷️  RISK CATEGORIES (from moderation):")
        categories = {}
        for r in results:
            if r['flagged_by_moderation'] and r['category']:
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
        print(f"\n⚠️  CRITICAL: {false_negatives} RISK MESSAGES WERE COMPLETELY MISSED!")
        print("   These phrases should be flagged but NEITHER system caught them:")
        for r in results:
            if r['true_label'] == 'Risk' and not r['flagged_overall']:
                print(f"      [{r['id']}] {r['text'][:70]}...")

    # Save detailed results
    output_file = os.path.join(
        os.path.dirname(__file__),
        f"complete_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'id', 'text', 'true_label', 'flagged_overall',
            'flagged_by_keywords', 'flagged_by_moderation', 'flagged_by_mh_ai',
            'mh_confidence', 'detection_method', 'category', 'correct'
        ])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n💾 Detailed results saved to:")
    print(f"   {output_file}")
    print("="*70)

if __name__ == "__main__":
    csv_file = os.path.join(os.path.dirname(__file__), 'mindmitra_risk_test_dataset.csv')

    if not os.path.exists(csv_file):
        print(f"❌ Error: Test dataset not found: {csv_file}")
        sys.exit(1)

    test_complete_risk_detection(csv_file)
