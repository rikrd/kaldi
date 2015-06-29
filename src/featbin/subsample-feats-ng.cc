// featbin/subsample-feats.cc

// Copyright 2012-2014  Johns Hopkins University (author: Daniel Povey)

// See ../../COPYING for clarification regarding multiple authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//  http://www.apache.org/licenses/LICENSE-2.0
//
// THIS CODE IS PROVIDED *AS IS* BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION ANY IMPLIED
// WARRANTIES OR CONDITIONS OF TITLE, FITNESS FOR A PARTICULAR PURPOSE,
// MERCHANTABLITY OR NON-INFRINGEMENT.
// See the Apache 2 License for the specific language governing permissions and
// limitations under the License.

#include <sstream>
#include <algorithm>
#include <iterator>
#include <utility>

#include "base/kaldi-common.h"
#include "util/common-utils.h"
#include "util/table-types.h"
#include "matrix/kaldi-matrix.h"


int main(int argc, char *argv[]) {
  try {
    using namespace kaldi;
    using namespace std;
    
    const char *usage =
        "Sub-samples features by taking every n'th frame."
        "Works in the same way as subsample-feats but the n is an rspecifier.\n"
        "This allows to have different n per utterance.\n"
        "\n"
        "Usage: subsample-feats-ng [options] <subsample-rspecifier> <in-rspecifier> <out-wspecifier>\n"
        "  e.g. subsample-feats-ng ark:n.ark ark:- ark:-\n";
    
    ParseOptions po(usage);
    
    int32 offset = 0;

    po.Register("offset", &offset, "Start with the feature with this offset, "
                "then take every n'th feature.");
    
    po.Read(argc, argv);
    
    if (po.NumArgs() != 3) {
      po.PrintUsage();
      exit(1);
    }    

    string subsample_rspecifier = po.GetArg(1);
    string rspecifier = po.GetArg(2);
    string wspecifier = po.GetArg(3);
    
    SequentialBaseFloatMatrixReader feat_reader(rspecifier);
    RandomAccessInt32Reader subsample_reader(subsample_rspecifier);
    BaseFloatMatrixWriter feat_writer(wspecifier);

    int32 num_done = 0, num_err = 0;
    int64 frames_in = 0, frames_out = 0;
    
    // process all keys
    for (; !feat_reader.Done(); feat_reader.Next()) {
      std::string utt = feat_reader.Key();
      const Matrix<BaseFloat> feats(feat_reader.Value());

      int32 n = subsample_reader.Value(utt);

      if (n > 0) {
        // This code could, of course, be much more efficient; I'm just
        // keeping it simple.
        int32 num_indexes = 0;
        for (int32 k = offset; k < feats.NumRows(); k += n)
          num_indexes++; // k is the index.

        frames_in += feats.NumRows();
        frames_out += num_indexes;
      
        if (num_indexes == 0) {
          KALDI_WARN << "For utterance " << utt << ", output would have no rows, "
                     << "producing no output.";
          num_err++;
          continue;
        }
        Matrix<BaseFloat> output(num_indexes, feats.NumCols());
        int32 i = 0;
        for (int32 k = offset; k < feats.NumRows(); k += n, i++) {
          SubVector<BaseFloat> src(feats, k), dest(output, i);
          dest.CopyFromVec(src);
        }
        KALDI_ASSERT(i == num_indexes);
        feat_writer.Write(utt, output);
        num_done++;
      } else {
        int32 repeat = -n;
        Matrix<BaseFloat> output(feats.NumRows() * repeat, feats.NumCols());
        for (int32 i = 0; i < output.NumRows(); i++)
          output.Row(i).CopyFromVec(feats.Row(i / repeat));
        frames_in += feats.NumRows();
        frames_out += feats.NumRows() * repeat;
        feat_writer.Write(utt, output);        
        num_done++;
      }
    }
    KALDI_LOG << "Processed " << num_done << " feature matrices; " << num_err
              << " with errors.";
    KALDI_LOG << "Processed " << frames_in << " input frames and "
              << frames_out << " output frames.";
    return (num_done != 0 ? 0 : 1);
  } catch(const std::exception &e) {
    std::cerr << e.what();
    return -1;
  }
}
