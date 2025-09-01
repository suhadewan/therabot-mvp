#!/usr/bin/env python3
"""
Benchmark Script for Integrated Extractor
Automatically tracks performance metrics and timing for each file
"""

import os
import time
import json
import csv
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from integrated_extractor import IntegratedExtractor


class ExtractorBenchmark:
    def __init__(self, va_api_key):
        self.extractor = IntegratedExtractor(va_api_key)
        self.results = []
        
    def benchmark_single_file(self, pdf_path, output_dir):
        """Benchmark a single PDF file with timing"""
        start_time = time.time()
        file_size = os.path.getsize(pdf_path)
        
        try:
            # Create output subdirectory for this file
            file_name = Path(pdf_path).stem
            file_output_dir = os.path.join(output_dir, file_name)
            os.makedirs(file_output_dir, exist_ok=True)
            
            # Run extraction
            results = self.extractor.extract_financial_statements(pdf_path, file_output_dir)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Extract classification info
            classification_results = {}
            if hasattr(results, 'classification_results'):
                classification_results = results.classification_results
            
            result = {
                'file_name': os.path.basename(pdf_path),
                'file_path': pdf_path,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'processing_time_seconds': round(processing_time, 2),
                'status': 'success',
                'output_dir': file_output_dir,
                'classification_results': classification_results,
                'error': None  # Add error field for consistency
            }
            
            print(f"✅ {os.path.basename(pdf_path)}: {processing_time:.2f}s ({file_size / (1024 * 1024):.1f}MB)")
            return result
            
        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            
            result = {
                'file_name': os.path.basename(pdf_path),
                'file_path': pdf_path,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'processing_time_seconds': round(processing_time, 2),
                'status': 'failed',
                'output_dir': None,
                'classification_results': {},  # Add empty classification_results for consistency
                'error': str(e)
            }
            
            print(f"❌ {os.path.basename(pdf_path)}: FAILED after {processing_time:.2f}s - {str(e)}")
            return result
    
    def benchmark_directory(self, input_dir, output_dir, max_workers=4, skip_existing=True):
        """Benchmark all PDFs in a directory using parallel processing"""
        if not os.path.exists(input_dir):
            raise ValueError(f"Input directory does not exist: {input_dir}")
        
        # Find all PDF files
        pdf_files = []
        for file in os.listdir(input_dir):
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(input_dir, file))
        
        if not pdf_files:
            raise ValueError(f"No PDF files found in: {input_dir}")
        
        # Filter out already processed files if skip_existing is True
        if skip_existing:
            filtered_files = []
            skipped_count = 0
            
            for pdf_path in pdf_files:
                file_name = Path(pdf_path).stem
                file_output_dir = os.path.join(output_dir, file_name)
                
                if os.path.exists(file_output_dir):
                    print(f"⏭️  Skipping {os.path.basename(pdf_path)} - already processed")
                    skipped_count += 1
                else:
                    filtered_files.append(pdf_path)
            
            pdf_files = filtered_files
            
            if skipped_count > 0:
                print(f"⏭️  Skipped {skipped_count} already processed files")
                print(f"📁 Remaining files to process: {len(pdf_files)}")
                print()
        
        if not pdf_files:
            print("✅ All files have already been processed!")
            return []
        
        print(f"🚀 Starting bulk benchmark of {len(pdf_files)} PDF files...")
        print(f"📁 Input: {input_dir}")
        print(f"📁 Output: {output_dir}")
        print(f"⚡ Parallel workers: {max_workers}")
        print(f"⏭️  Skip existing: {skip_existing}")
        print("-" * 60)
        
        # Create output directory (use exact name specified by user)
        os.makedirs(output_dir, exist_ok=True)
        
        # Track start time for overall benchmark
        overall_start_time = time.time()
        
        # Process files in parallel with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self.benchmark_single_file, pdf_path, output_dir): pdf_path 
                for pdf_path in pdf_files
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_file):
                result = future.result()
                self.results.append(result)
                
                # Save intermediate results after each file
                self._save_results(output_dir)
        
        # Calculate overall statistics
        overall_end_time = time.time()
        total_time = overall_end_time - overall_start_time
        
        # Generate final report
        self._generate_report(total_time, len(pdf_files))
        
        return self.results
    
    def _save_results(self, output_dir):
        """Save benchmark results to JSON and CSV"""
        # Save to JSON
        json_path = os.path.join(output_dir, 'benchmark_results.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        # Save to CSV
        csv_path = os.path.join(output_dir, 'benchmark_results.csv')
        if self.results:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.results[0].keys())
                writer.writeheader()
                writer.writerows(self.results)
    
    def _generate_report(self, total_time, total_files):
        """Generate and print benchmark report"""
        if not self.results:
            print("❌ No results to report")
            return
        
        successful = [r for r in self.results if r['status'] == 'success']
        failed = [r for r in self.results if r['status'] == 'failed']
        
        success_rate = (len(successful) / total_files) * 100 if total_files > 0 else 0
        
        if successful:
            times = [r['processing_time_seconds'] for r in successful]
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            files_per_minute = (len(successful) / total_time) * 60
        else:
            avg_time = min_time = max_time = files_per_minute = 0
        
        print("\n" + "=" * 60)
        print("📊 BENCHMARK RESULTS SUMMARY")
        print("=" * 60)
        print(f"📁 Total files processed: {total_files}")
        print(f"✅ Successful: {len(successful)}")
        print(f"❌ Failed: {len(failed)}")
        print(f"📈 Success rate: {success_rate:.1f}%")
        print(f"⏱️  Total benchmark time: {total_time:.2f} seconds")
        print(f"🚀 Files per minute: {files_per_minute:.1f}")
        print()
        print("⏱️  Individual File Performance:")
        print(f"   • Average time: {avg_time:.2f} seconds")
        print(f"   • Fastest: {min_time:.2f} seconds")
        print(f"   • Slowest: {max_time:.2f} seconds")
        print()
        
        if failed:
            print("❌ Failed Files:")
            for result in failed:
                print(f"   • {result['file_name']}: {result.get('error', 'Unknown error')}")
        
        print("=" * 60)
        print(f"📊 Detailed results saved to: {os.path.join(output_dir, 'benchmark_results.json')}")
        print(f"📊 CSV results saved to: {os.path.join(output_dir, 'benchmark_results.csv')}")


def run_benchmark(input_dir, output_dir, va_api_key, max_workers=4, skip_existing=True):
    """Run the benchmark on a directory of PDFs"""
    benchmark = ExtractorBenchmark(va_api_key)
    return benchmark.benchmark_directory(input_dir, output_dir, max_workers, skip_existing)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Benchmark the IntegratedExtractor performance')
    parser.add_argument('--input-dir', required=True, help='Directory containing PDF files to benchmark')
    parser.add_argument('--output-dir', required=True, help='Directory to save benchmark results and extracted data')
    parser.add_argument('--va-api-key', required=True, help='Vision Agent API key')
    parser.add_argument('--max-workers', type=int, default=4, help='Maximum number of parallel workers (default: 4)')
    parser.add_argument('--no-skip-existing', action='store_true', help='Process all files, even if already processed')
    
    args = parser.parse_args()
    
    try:
        skip_existing = not args.no_skip_existing
        run_benchmark(args.input_dir, args.output_dir, args.va_api_key, args.max_workers, skip_existing)
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        exit(1) 