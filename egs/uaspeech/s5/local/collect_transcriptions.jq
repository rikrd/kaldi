reduce inputs as $line
({};
    (input_filename | split("/")) as $exp_tokens
    | ($line | split(" ")) as $tokens
    | ($tokens[1:] | join(" ") | rtrimstr(" ")) as $transcription
    | ($exp_tokens[:-2] | join("/")) as $exp_key
    | (if $exp_tokens[-1]=="test_filt.txt" then "reference" else "transcription" end) as $transcription_key
    | . * {($exp_key):
                {
                    exp: $exp_tokens[-7],
                    exp_param: $exp_tokens[-6],
                    task: $exp_tokens[-3],
                    model: $exp_tokens[-4],
                    utterances: {
                        ($tokens[0]): {
                            #($transcription_key): $transcription,
                            ($transcription_key + "_normalized"): ($transcription | sub("\\(\\d+\\)$"; "") )
                        }
                    }
                }
            }
)