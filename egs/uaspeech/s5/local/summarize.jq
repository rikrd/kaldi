reduce values[] as $value
({};
($value.exp + "/" + $value.exp_param + "/" + $value.task + "/" + $value.model) as $id
| .[$id].matches as $matches
| .[$id].total as $total
| . * {($id): {matches: ($matches+(if $value.transcription_normalized==$value.reference_normalized
                                   then 1
                                   else 0
                                   end)),
               total: ($total+1)}}
)