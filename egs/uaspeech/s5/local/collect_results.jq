(input_filename | split("/")) as $exp_tokens
 | split(" ") as $tokens
 | {exp: $exp_tokens[-7],
    exp_param: $exp_tokens[-6],
    task: $exp_tokens[-3],
    model: $exp_tokens[-4],
    uttid: $tokens[0],
    transcription: ($tokens[1:] | join(" "))}