reduce values[] as $value
({};
($value.exp + "_" + $value.exp_param + "_" + $value.task + "_" + $value.model) as $id
| .[$id].matches as $matches
| .[$id].total as $total
| . * {($id): {matches: ($matches+(if $value.transcription_normalized==$value.reference_normalized
                                   then 1
                                   else 0
                                   end)),
               total: ($total+1)}}
)