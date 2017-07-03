import json
import os
import sys

def load_src(name, fpath):
    import os, imp
    return imp.load_source(name, os.path.join(os.path.dirname(__file__), fpath))

load_src("twic_text", os.path.join("lib", "twic", "general", "twic_text.py"))
from twic_text import TWiC_Text
load_src("twic_malletinterpret", os.path.join("lib", "twic", "general", "twic_malletinterpret.py"))
from twic_malletinterpret import TWiC_MalletInterpret
load_src("twic_malletscript", os.path.join("lib", "twic", "general", "twic_malletscript.py"))
from twic_malletscript import TWiC_MalletScript
load_src("utils_malletinterpret", os.path.join("lib", "twic", "utils", "utils_malletinterpret.py"))
from utils_malletinterpret import Utils_MalletInterpret
load_src("utils_color", os.path.join("lib", "twic", "utils", "utils_color.py"))
from utils_color import Utils_Color


def strip_punctuation(p_word):

    # Lowercase and clear whitespace
    p_word = p_word.lower().strip()

    # Find the first and last alphabetic characters
    first_index = 0
    found_alnum = False
    for index in range(len(p_word)):
        if str(p_word[index]).isalnum():
            first_index = index
            found_alnum = True
            break
    last_index = len(p_word) - 1
    for index in reversed(range(len(p_word))):
        if str(p_word[index]).isalnum():
            last_index = index
            found_alnum = True
            break

    # Strip outside non-alphabetic characters
    p_word = p_word[first_index:last_index + 1] if found_alnum else ""

    return p_word


def read_yaml():

    yaml_filepath = os.getcwd() + os.sep + "tcr_config.yaml"
    
    if not os.path.isfile(yaml_filepath):
        return None
        
    with open(yaml_filepath, "rU") as yaml_file:
        yaml_dict = {}
        yaml_lines = yaml_file.readlines()
        for line in yaml_lines:
            parts = line.split(":")
            yaml_dict[parts[0].strip()] = parts[1].strip()

    return yaml_dict


def load_topic_model_data(p_tcr_config):

    try:

        # Create a TWiC_MalletScript object (twic_malletscript.yp req. is inferred)
        mallet_script = TWiC_MalletScript()

        # Set path for MALLET files
        mallet_script.output_dir = p_tcr_config["output_path"]

        # Set path for input corpus texts
        mallet_script.corpus_source_dir = p_tcr_config["corpus_path"]

        # Set file names (must prepend mallet_script.output_dir)
        mallet_script.topics_file = p_tcr_config["mallet_files_path"] + p_tcr_config["mallet_topicweights_file"]
        mallet_script.keys_file = p_tcr_config["mallet_files_path"] + p_tcr_config["mallet_topics_file"]
        mallet_script.state_file = p_tcr_config["mallet_files_path"] + p_tcr_config["mallet_state_file"]
        mallet_script.wordweights_file = p_tcr_config["mallet_files_path"] + p_tcr_config["mallet_wordweights_file"]

        # Set corpus title
        TWiC_MalletScript.corpus_title = p_tcr_config["corpus_title"]

        # Get topics file data (corpus.topics.tsv)
        tp_collection = mallet_script.GetTopicsFileData("2.0.9")

        # Get topic keys data (corpus.keys.tsv)
        topic_keys = mallet_script.GetKeysFileData()

        # Get topic words state data (corpus.topic-state.tsv)
        fwt_collection = mallet_script.GetStateFileData()

        # Get topic word weights data (corpus.wordweights.tsv)
        ww_table = mallet_script.GetTopicWordWeights()

        # Generated color list (utils_color.py req. is inferred, Also palette-preference options?)
        color_list = Utils_Color.Get_UniqueColorList(len(topic_keys.corpus_topic_proportions.keys()))

    except:
        print "Error loading topic model data: {0}".format(sys.exc_info()[0])
        return None

    return [tp_collection, topic_keys, fwt_collection, ww_table, color_list, mallet_script]


def create_model_json_for_texts(p_mallet_script, p_tp_collection, p_fwt_collection):

    # Need to build a text object (TWiC_Text) for each class
    textobj_collection = TWiC_MalletInterpret.Build_TextObjects_Opt(TWiC_Text, p_mallet_script, p_tp_collection)

    # Create in-memory JSON objects that merge each mentioned text with topic word data from the MALLET state file
    twic_texts_json = {}
    for text in textobj_collection:
        current_fwt = None
        file_id = text.GetFilename()
        for fwt in p_fwt_collection:
            fwt_file_id = Utils_MalletInterpret.GetFilename(fwt.GetFilename())
            if fwt_file_id == file_id:
                current_fwt = fwt
                break            
        text_json = TWiC_MalletInterpret.ConvertTextToJSON(text, "", p_mallet_script, current_fwt, False)
        if "No state file data" == text_json:
            text_json = None
        twic_texts_json[file_id + text.GetFileExtension()] = text_json

    return twic_texts_json


def create_ordered_data_structures(p_twic_text_json, p_tp_collection, p_topic_count, p_ww_table):

    # Dictionary of topic proportions keyed on filename
    twic_text_topicweights = {}
    for text_filename in p_twic_text_json:
        found = False
        for tp in p_tp_collection:
            if tp.fileid + ".txt" == text_filename:
                twic_text_topicweights[text_filename] = tp.topic_guide
                found = True
                break
        if not found:
            print "Could not find {0}".format(text_filename)

    # Create an ordered topic word weight list (this will be used to rank topic words within their topic)
    ord_topic_word_weights = []
    for index in range(p_topic_count):
        ord_topic_word_weights.append([])
        for word_key in p_ww_table[str(index)]:
            ord_topic_word_weights[index].append((word_key, p_ww_table[str(index)][word_key]))
        ord_topic_word_weights[index] = sorted(ord_topic_word_weights[index], key=lambda x: x[1], reverse=True)

    # Create an ordered topic weight list for texts (this will be used to rank topics by their texts)
    ord_topics_in_texts = {}
    for text_filename in p_twic_text_json:
        ord_topics_in_texts[text_filename] = []
        for index in range(p_topic_count):
            ord_topics_in_texts[text_filename].append((index, twic_text_topicweights[text_filename][str(index)]))
        ord_topics_in_texts[text_filename] = sorted(ord_topics_in_texts[text_filename], key=lambda x: x[1], reverse=True)


    return [twic_text_topicweights, ord_topic_word_weights, ord_topics_in_texts]


def read_hover_code():

    hover_js_filepath = os.getcwd() + os.sep + "js" + os.sep + "tcr_hover_code.js"

    if not os.path.isfile(hover_js_filepath):
        return None

    hover_js_lines = []
    with open(hover_js_filepath, "rU") as hover_js_file:
        hover_js_lines = hover_js_file.readlines()
        for index in range(len(hover_js_lines)):
            hover_js_lines[index] = "\t\t\t" + hover_js_lines[index]

    return hover_js_lines


def main():

    print "\nTopic Words in Context (TWiC) Close Reading"
    print "\tby Jonathan Armoza (github.com/jarmoza), 2017.\n"
    print "This work is licensed under a"
    print "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.\n"

    # 1. Read MALLET filenames, output path
    print "Reading YAML file..."
    tcr_config = read_yaml()
    if None == tcr_config:
        print "Could not find YAML file."
        return
    
    # 2. Load MALLET topic model data into TWiC data structures
    print "Reading MALLET files..."
    model_data = load_topic_model_data(tcr_config)
    if None == model_data:
        return
    tp_collection, topic_keys, fwt_collection, ww_table, color_list, mallet_script = model_data

    # 3. Gather required topic model information
    print "Gathering model information into memory..."

    # Text information
    twic_text_json = create_model_json_for_texts(mallet_script, tp_collection, fwt_collection)

    # Topic information
    topic_count = len(color_list)
    topic_list = topic_keys.corpus_topic_words

    # Create several ordered data structure for file topic weights and topic word weights
    twic_text_topicweights, ord_topic_word_weights, ord_topics_in_texts = \
        create_ordered_data_structures(twic_text_json, tp_collection, topic_count, ww_table)

    # 4. Read in JavaScript code for topic word-highlight hovering
    print "Reading in TWiC close reading hover code..."
    hover_js_lines = read_hover_code()
    if None == hover_js_lines:
        print "Could not find hover JavaScript."
        return

    # tcr_config, ww_table, color_list, twic_text_json, topic_count, topic_list
    # twic_text_topicweights, ord_topic_word_weights, ord_topics_in_texts, hover_js_lines

    # 5. Build close-reading HTML files
    print "Building close reading HTML files..."

    small_word_weight = 0.0000000001
    # font_size_min = 12 # Weight-Font size functionality is disabled in this implementation
    # font_size_max = 48 # 4x the minimum size
    topic_word_id_table = {}
    present_topics = []
    html_files_output = 0

    for text_filename in twic_text_json:

        # a. Create tables for internal topic-word id, and word/weight/rank information

        # Gather composite weights
        ordered_word_list = []

        # If no data was found for a text in MALLET's topic-state file, continue on to the next text in the corpus
        if None == twic_text_json[text_filename]:
            print "No MALLET topic-state data found for {0}. Could not make HTML file.".format(text_filename)
            continue

        # Keep track of number of files outputted (w/ MALLET topic state files)
        html_files_output += 1

        for line_index in range(len(twic_text_json[text_filename]["document"]["lines_and_colors"])):           

            for word_index in range(len(twic_text_json[text_filename]["document"]["lines_and_colors"][line_index][0])):

                if str(word_index) in twic_text_json[text_filename]["document"]["lines_and_colors"][line_index][1]:
                    
                    word_topic_id = twic_text_json[text_filename]["document"]["lines_and_colors"][line_index][1][str(word_index)]
                    present_topics.append(word_topic_id)
                    word = twic_text_json[text_filename]["document"]["lines_and_colors"][line_index][0][word_index]
                    text_topic_weight = twic_text_topicweights[text_filename][word_topic_id]
                    word_sans_punc = strip_punctuation(word)

                    # Add this word to the topic_word_id_table (assigns class numeric word IDs)
                    if word_topic_id not in topic_word_id_table:
                        topic_word_id_table[word_topic_id] = { "last_id": 0 }
                    topic_word_id_table[word_topic_id][word_sans_punc] = topic_word_id_table[word_topic_id]["last_id"]
                    topic_word_id_table[word_topic_id]["last_id"] += 1                    

                    if word_sans_punc in ww_table[word_topic_id]:
                        topic_word_weight = ww_table[word_topic_id][word_sans_punc]
                    else:
                        topic_word_weight = small_word_weight

                    ordered_word_list.append((word, word_index * (line_index + 1), text_topic_weight * topic_word_weight,
                        word_index, line_index, text_topic_weight, topic_word_weight, word_topic_id))
                else:
                    word = twic_text_json[text_filename]["document"]["lines_and_colors"][line_index][0][word_index]
                    ordered_word_list.append((word, word_index * (line_index + 1), -1, word_index, line_index))

        # Sort word tuples by composite weights
        ordered_word_list = sorted(ordered_word_list, key=lambda x: x[2])

        # Divide the font size range by the number of words
        # font_increment = (font_size_max - font_size_min) / float(len(ordered_word_list))

        # Make a set of all topics present in this file
        present_topics = list(set(present_topics))

        # Create the word rank table (ordered by composite weight - document-topic weight * topic-word weight)
        # font_size_table = {}
        prev_composite_value = ordered_word_list[0][2]
        shift_index = 0
        ordered_indices = {}
        for index in range(len(ordered_word_list)):
            if ordered_word_list[index][2] != prev_composite_value:
                shift_index = index
                prev_composite_value = ordered_word_list[index][2]
            # font_size_table[ordered_word_list[index][1]] = font_size_min + (shift_index * font_increment)
            ordered_indices[ordered_word_list[index][1]] = len(ordered_word_list) - shift_index

        # b. Write out the HTML file
        with open(tcr_config["output_path"] + os.path.splitext(text_filename)[0] + ".html", "w") as output_html_file:

            output_html_file.write("<!DOCTYPE html>\n")
            output_html_file.write("<html>\n")

            output_html_file.write("\t<head>\n")

            output_html_file.write("\t\t<meta charset=\"utf-8\">\n")
            output_html_file.write("\t\t<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n")
            
            # All JS and CSS are stored within the output folder for ease of use, copying, etc.
            output_html_file.write("\t\t<link rel=\"stylesheet\" type=\"text/css\" href=\"bootstrap.min.css\">\n")
            output_html_file.write("\t\t<link rel=\"stylesheet\" type=\"text/css\" href=\"twic_close_reading.css\">\n")
            output_html_file.write("\t\t<script src=\"jquery-3.2.1.min.js\"></script>\n")
            output_html_file.write("\t\t<script src=\"bootstrap.min.js\"></script>\n")

            # Output hover JS code and custom topic word highlighting JS code            
            output_html_file.write("\t\t<script>\n")
            for line in hover_js_lines:
                output_html_file.write(line)    
            output_html_file.write("\n\n")
            output_html_file.write("\t\t\t$(function(){\n\n")

            for index in range(len(present_topics)):
                output_html_file.write("\t\t\t\t$(\"span.topic{0}\").hover(HoverEnter, HoverExit);\n".format(present_topics[index]))
                output_html_file.write("\t\t\t\ttopicColorTable[\"topic{0}\"] = $(\"span.topic{0}\").css(\"color\");\n".format(present_topics[index]))
            output_html_file.write("\t\t\t});\n")
            output_html_file.write("\t\t</script>\n")

            # Output custom CSS
            output_html_file.write("\t\t<style>\n")
            for index in range(len(present_topics)):
                output_html_file.write("\t\t\t.topic{0} {{\n".format(present_topics[index]))
                output_html_file.write("\t\t\t\tcolor: {0};\n".format(color_list[int(present_topics[index])]))
                output_html_file.write("\t\t\t}\n\n")
            output_html_file.write("\t\t</style>\n")
            output_html_file.write("\t</head>\n")
            
            output_html_file.write("\t<body>\n")

            output_html_file.write("\t\t<div class=\"container-fluid\">\n")
            output_html_file.write("\t\t\t<div class=\"row table-row\">\n")
            text_column_width = 7
            output_html_file.write("\t\t\t\t<div class=\"col-xs-{0} col-sm-{0} col-md-{0} col-lg-{0}\">\n".format(text_column_width))

            for line_index in range(len(twic_text_json[text_filename]["document"]["lines_and_colors"])):
                output_html_file.write("\t\t\t\t\t<p>")
                for word_index in range(len(twic_text_json[text_filename]["document"]["lines_and_colors"][line_index][0])):
                    
                    if str(word_index) in twic_text_json[text_filename]["document"]["lines_and_colors"][line_index][1]:
                        
                        word_topic_id = twic_text_json[text_filename]["document"]["lines_and_colors"][line_index][1][str(word_index)]
                        word_color = color_list[int(word_topic_id)]
                        word = twic_text_json[text_filename]["document"]["lines_and_colors"][line_index][0][word_index]
                        word_sans_punc = strip_punctuation(word)
                        text_topic_weight = twic_text_topicweights[text_filename][word_topic_id]

                        if word_sans_punc in ww_table[word_topic_id]:
                            topic_word_weight = ww_table[word_topic_id][word_sans_punc]
                        else:
                            topic_word_weight = small_word_weight
                        
                        # output_html_file.write("<span style=\"color:{0}; font-size:{1}px;\">{2}({3},{4})&nbsp;</span>".format(
                        #     word_color, 
                        #     font_size_table[word_index * (line_index + 1)],
                        #     word,
                        #     1 + ordered_indices[word_index * (line_index + 1)],
                        #     text_topic_weight * topic_word_weight))

                        # output_html_file.write("<span style=\"color:{0}; \">{1}({2},{3})&nbsp;</span>".format(
                        #     word_color, 
                        #     word,
                        #     1 + ordered_indices[word_index * (line_index + 1)],
                        #     text_topic_weight * topic_word_weight))

                        output_html_file.write("<span class=\"topicword topic{0} topic{1}_{2}\" style=\"color:{3};\">{4}</span><span>&nbsp;</span>".format(
                            word_topic_id,
                            word_topic_id,
                            topic_word_id_table[word_topic_id][word_sans_punc],
                            word_color, 
                            word))

                    else:
                        output_html_file.write("<span class=\"normword\">{0}</span><span>&nbsp;</span>".format( 
                            twic_text_json[text_filename]["document"]["lines_and_colors"][line_index][0][word_index]))
                output_html_file.write("</p><br/>\n")

            output_html_file.write("\t\t\t\t</div>\n") # End Column
            weights_column_width = 5
            output_html_file.write("\t\t\t\t<div class=\"col-xs-{0} col-sm-{0} col-md-{0} col-lg-{0} wordweightcolumn\">\n".format(weights_column_width))

            list_index = 0
            current_word = strip_punctuation(ordered_word_list[0][0])
            output_html_file.write("\t\t\t\t\t<p><span class=\"normword\">Composite Rank. (doc topic rank, topic word rank)</span></p><br/>\n")
            for index in reversed(range(len(ordered_word_list))):
                if str(ordered_word_list[index][3]) in twic_text_json[text_filename]["document"]["lines_and_colors"][ordered_word_list[index][4]][1]:
                    word_sans_punc = strip_punctuation(ordered_word_list[index][0])
                    if word_sans_punc != current_word:
                        current_word = word_sans_punc
                        list_index += 1
                    word_topic_id = twic_text_json[text_filename]["document"]["lines_and_colors"][ordered_word_list[index][4]][1][str(ordered_word_list[index][3])]
                    word_color = color_list[int(word_topic_id)]                
                    doc_topic_rank = -1
                    for index2 in range(topic_count):
                        if int(word_topic_id) == ord_topics_in_texts[text_filename][index2][0]:
                            doc_topic_rank = index2 + 1
                            break
                    topic_word_rank = -1
                    int_word_topic_id = int(word_topic_id)
                    for index2 in range(len(ord_topic_word_weights[int_word_topic_id])):
                        if word_sans_punc == ord_topic_word_weights[int_word_topic_id][index2][0]:
                            topic_word_rank = index2 + 1
                            break
                    output_html_file.write("\t\t\t\t\t<p><span class=\"topicword topic{0} topic{0}_{1}\" style=\"color:{2}\">{3}. {4} ({5}, {6})</span></p><br/>\n".format(
                        word_topic_id,
                        topic_word_id_table[word_topic_id][word_sans_punc],
                        word_color,                        
                        list_index,
                        word_sans_punc,
                        doc_topic_rank,
                        topic_word_rank))
            output_html_file.write("\t\t\t\t</div>\n") # End Column
            output_html_file.write("\t\t\t</div>\n") # End Row
            output_html_file.write("\t\t</div>\n") # End Container

            output_html_file.write("\t\t<footer class=\"footer\">\n")

            output_html_file.write("\t\t\t<div class\"container-fluid\">\n")

            output_html_file.write("\t\t\t\t<div class=\"row\">\n")
            output_html_file.write("\t\t\t\t\t<p><span class=\"topicword topicwordlist\">Topic Word List</span></p><br/>\n")
            output_html_file.write("\t\t\t\t</div>\n")

            output_html_file.write("\t\t\t\t<div class=\"row meta_row\">\n")

            output_html_file.write("\t\t\t\t\t<div class=\"col-xs-{0} col-sm-{0} col-md-{0} col-lg-{0}\">\n".format(2))
            output_html_file.write("\t\t\t\t\t\t<p><span class=\"normword meta_label\">Word:&nbsp;</span>")
            output_html_file.write("<span class=\"meta_topicword\"></span></p><br/>\n")
            output_html_file.write("\t\t\t\t\t</div>") # End Col

            output_html_file.write("\t\t\t\t\t<div class=\"col-xs-{0} col-sm-{0} col-md-{0} col-lg-{0}\">\n".format(10))
            output_html_file.write("\t\t\t\t\t\t<p><span class=\"normword meta_label\">Composite Rank:&nbsp;</span>")
            output_html_file.write("<span class=\"topicword compositerank\"></span></p><br/>\n")
            output_html_file.write("\t\t\t\t\t\t<p><span class=\"normword meta_label\">Document-Topic Rank:&nbsp;</span>")
            output_html_file.write("<span class=\"topicword doctopicrank\"></span></p><br/>\n")
            output_html_file.write("\t\t\t\t\t\t<p><span class=\"normword meta_label\">Topic-Word Rank:&nbsp;</span>")
            output_html_file.write("<span class=\"topicword topicwordrank\"></span></p><br/>\n")
            output_html_file.write("\t\t\t\t\t</div>\n") # End Col

            output_html_file.write("\t\t\t\t</div>\n") # End Row

            # Invisible topic word lists - their text will go into the visible topic word list span
            for index in range(topic_count):
                output_html_file.write("\t\t\t\t<p><span class=\"invisible_topicwordlist topic{0}\">Topic {0}: {1}</span></p>\n".format(index, 
                    ", ".join(topic_list[str(index)])))

            # Invisible word stats - their text will go into the visible topic word list span
            list_index = 0
            current_word = strip_punctuation(ordered_word_list[0][0])            
            for index in reversed(range(len(ordered_word_list))):
                if str(ordered_word_list[index][3]) in twic_text_json[text_filename]["document"]["lines_and_colors"][ordered_word_list[index][4]][1]:
                    word_sans_punc = strip_punctuation(ordered_word_list[index][0])
                    if word_sans_punc != current_word:
                        current_word = word_sans_punc
                        list_index += 1
                    word_topic_id = twic_text_json[text_filename]["document"]["lines_and_colors"][ordered_word_list[index][4]][1][str(ordered_word_list[index][3])]
                    word_color = color_list[int(word_topic_id)]                
                    doc_topic_rank = -1
                    for index2 in range(topic_count):
                        if int(word_topic_id) == ord_topics_in_texts[text_filename][index2][0]:
                            doc_topic_rank = index2 + 1
                            break
                    topic_word_rank = -1
                    int_word_topic_id = int(word_topic_id)
                    for index2 in range(len(ord_topic_word_weights[int_word_topic_id])):
                        if word_sans_punc == ord_topic_word_weights[int_word_topic_id][index2][0]:
                            topic_word_rank = index2 + 1
                            break
                    output_html_file.write("\t\t\t\t<p><span class=\"invisible_topicword topic{0} topic{0}_{1}\">{2}</span></p>\n".format(
                        word_topic_id,
                        topic_word_id_table[word_topic_id][word_sans_punc],
                        word_sans_punc))
                    output_html_file.write("\t\t\t\t<p><span class=\"invisible_compositerank topic{0} topic{0}_{1}\">{2}</span></p>\n".format(
                        word_topic_id,
                        topic_word_id_table[word_topic_id][word_sans_punc],
                        list_index))
                    output_html_file.write("\t\t\t\t<p><span class=\"invisible_doctopicrank topic{0} topic{0}_{1}\">{2}</span></p>\n".format(
                        word_topic_id,
                        topic_word_id_table[word_topic_id][word_sans_punc],
                        doc_topic_rank))
                    output_html_file.write("\t\t\t\t<p><span class=\"invisible_topicwordrank topic{0} topic{0}_{1}\">{2}</span></p>\n".format(
                        word_topic_id,
                        topic_word_id_table[word_topic_id][word_sans_punc],
                        topic_word_rank))                

            output_html_file.write("\t\t\t</div>\n") # End Container
            output_html_file.write("\t\t</footer>\n") # End Footer

            output_html_file.write("\t</body>\n")
            output_html_file.write("</html>")

    print "Finished building HTML files for MALLET topic model of {0}.".format(tcr_config["corpus_title"])
    print "Could not find MALLET topic-state data for {0} files in this corpus.".format(len(twic_text_json) - html_files_output)
    print "Created {0} TWiC close reading HTML files in {1}.".format(html_files_output, tcr_config["output_path"])


if "__main__" == __name__:
    Utils_MalletInterpret.TimeAndRun(main, "TWiC Close Reading")