"""def code_repo(pmHandler):
    variants_count = case_statistics.get_variant_statistics(log=pmHandler.log)
    variants_count = sorted(variants_count, key=lambda x: x['count'], reverse=True)
    len_event, min_act_count = len(pmHandler.log), variants_count[floor(len(variants_count) * 0.1)]['count']

    count_act, act_count = {}, 0
    for case in pmHandler.log:
        for event in case:
            act = event['concept:name']
            act_count += 1
            if not act in count_act:
                count_act[act] = 1
            else:
                count_act[act] = count_act[act] + 1
    count_list = [{'activity': key, 'count': value} for key, value in count_act.items() if value > act_count * 0.05]
    count_list = sorted(count_list, key=lambda x: x['count'], reverse=True)
    count_least = count_list[-1]['count']
    print(count_list)
    print(f'length of event_log {len_event}\n, variant which presents the median {min_act_count}')
    result = search_best_parameters_heuristic_recursive(pmHandler, min_act_count, 1, 1000, 1, 1000, (1, 1, 0))
    print(f'The best score: {result[0]} with the min_act: {result[1]} and the min_occ{result[2]}')"""