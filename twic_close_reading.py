from datetime import datetime
import json
import logging
import os
import string
import sys
import traceback


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

# import numpy
# time_counter = 0
# times_profile = []
# def TimeAndCount(function, optional_text, *args):
#
#     global time_counter
#     global times_profile
#
#     # Run begins here
#     start_time = datetime.now()
#
#     retval = function(*args)
#
#     # Run finishes here
#     time_counter += (datetime.now() - start_time).total_seconds()
#
#     times_profile.append((optional_text, time_counter))
#
#     if "" != optional_text:
#         print "{0} finished".format(optional_text)
#
#     return retval
#
# def PrintTime():
#
#     global time_counter
#
#     print "This process took {0} seconds.\n".format(time_counter)
#
# def ResetTimer():
#
#     global time_counter
#
#     time_counter = 0
#
# def GetTime():
#
#     return datetime.now()
#
# def PrintAndReset():
#
#     PrintTime()
#     ResetTimer()
#
# def PrintTaskProfile():
#
#     global times_profile
#
#     time_sum = 0
#     for index in range(len(times_profile)):
#         time_sum += times_profile[index][1]
#     print "Total process time: {0}".format(time_sum)
#     for index in range(len(times_profile)):
#         print "\t{0} time: {1}%".format(times_profile[index][0], times_profile[index][1] / float(time_sum))


class TWiC_CloseReading:

    def __init__(self, p_tcr_root_folder, p_yaml_config_filename):

        # YAML containing TCR and MALLET configuration info
        self.m_tcr_root_folder = TWiC_CloseReading.ensure_folder_has_endsep(p_tcr_root_folder)
        self.m_yaml_config_filename = p_yaml_config_filename
        self.m_yaml_config = {}

        # Create a TWiC_MalletScript object (twic_malletscript.yp req. is inferred)
        self.m_mallet_script = TWiC_MalletScript()

        # TWiC Text-specific data
        self.m_twic_text_collection = []
        self.m_twic_texts_json = {}

        # Topic model data and data collections
        self.m_topic_count = 0
        self.m_topic_list = []
        self.m_text_topicweights = {}
        self.m_ord_words_in_topics = []
        self.m_stripped_ord_words_in_topics = []
        self.m_ord_topics_in_texts = {}
        self.m_last_topic_word_ranks = []

        # Custom JavaScript library info
        self.m_js_folder = self.m_tcr_root_folder + "js" + os.sep
        self.m_js_hovercode_filename = "tcr_hover_code.js"
        self.m_hover_js_lines = []

        # Twitter bootstrap column widths
        self.m_twitter_bootstrap_dims = {
            "cols_text" : 7,
            "cols_comprank_list" : 5,
            "cols_meta_topicword" : 2,
            "cols_meta_ranks" : 10
        }

        # HTML output metadata
        self.m_html_files_output = 0
        self.m_unprocessed_filenames = []
        self.m_tcr_unprocessed_filename = "tcr_unprocessed.txt"


    def read_yaml(self):

        yaml_filepath = "{0}{1}{2}".format(self.m_tcr_root_folder, os.sep, self.m_yaml_config_filename)

        if not os.path.isfile(yaml_filepath):
            raise IOError("Could not find YAML file '{0}' in {1}.".format(self.m_yaml_config_filename,
                                                                          self.m_yaml_config_folder))
        # Read all YAML fields
        with open(yaml_filepath, "rU") as yaml_file:
            yaml_lines = yaml_file.readlines()
            for line in yaml_lines:
                parts = line.split(":")
                self.m_yaml_config[parts[0].strip()] = parts[1].strip()

        # Ensure all paths end with os.sep
        for field in self.m_yaml_config:
            if "path" in field:
                self.m_yaml_config[field] = TWiC_CloseReading.ensure_folder_has_endsep(self.m_yaml_config[field])


    def load_topic_model_data(self):

        try:

            # Set path for output HTML files
            self.m_mallet_script.output_dir = self.m_yaml_config["output_path"]

            # Set path for input corpus texts
            self.m_mallet_script.corpus_source_dir = self.m_yaml_config["corpus_path"]

            # Set file names (must prepend m_mallet_script.output_dir)
            self.m_mallet_script.topics_file = self.m_yaml_config["mallet_files_path"] + self.m_yaml_config["mallet_topicweights_file"]
            self.m_mallet_script.keys_file = self.m_yaml_config["mallet_files_path"] + self.m_yaml_config["mallet_topics_file"]
            self.m_mallet_script.state_file = self.m_yaml_config["mallet_files_path"] + self.m_yaml_config["mallet_state_file"]
            self.m_mallet_script.wordweights_file = self.m_yaml_config["mallet_files_path"] + self.m_yaml_config["mallet_wordweights_file"]

            # Set corpus title
            TWiC_MalletScript.corpus_title = self.m_yaml_config["corpus_title"]

            # Get topics file data (corpus.topics.tsv)
            self.m_topics_file_data = self.m_mallet_script.GetTopicsFileData(self.m_yaml_config["mallet_version"])

            # Get topic keys data (corpus.keys.tsv)
            self.m_topic_keys = self.m_mallet_script.GetKeysFileData()

            # Get topic words state data (corpus.topic-state.tsv)
            self.m_topic_state_data = self.m_mallet_script.GetStateFileData()

            # Get topic word weights data (corpus.wordweights.tsv)
            self.m_wordweights_table = self.m_mallet_script.GetTopicWordWeights()

            # Generated color list and str version (utils_color.py req. is inferred, Also palette-preference options?)
            self.m_color_list_int = Utils_Color.Get_UniqueColorList(len(self.m_topic_keys.corpus_topic_proportions.keys()))
            self.m_color_list_str = {}
            for index in range(len(self.m_color_list_int)):
                self.m_color_list_str[str(index)] = self.m_color_list_int[index]

            # Topic information
            self.m_topic_count = len(self.m_color_list_int)
            self.m_topic_list = self.m_topic_keys.corpus_topic_words

        except Exception as exc:
            exc.message = "Error loading topic model data: {0}".format(sys.exc_info()[0])
            raise exc


    def convert_model_data_into_structures(self):

        # Text information
        self.create_model_json_for_texts()

        # Create several ordered data structure for file topic weights and topic word weights
        self.create_ordered_data_structures()


    def create_model_json_for_texts(self):

        # Need to build a text object (TWiC_Text) for each class
        self.m_twic_text_collection = TWiC_MalletInterpret.Build_TextObjects(TWiC_Text, self.m_mallet_script, self.m_topics_file_data)

        # Create in-memory JSON objects that merge each mentioned text with topic word data from the MALLET state file
        for text in self.m_twic_text_collection:
            current_fwt = None
            file_id = text.GetFilename()
            if file_id in self.m_topic_state_data:
                current_fwt = self.m_topic_state_data[text.GetFilename()]
            text_json = TWiC_MalletInterpret.ConvertTextToJSON(text, "", self.m_mallet_script, current_fwt, False)
            self.m_twic_texts_json[text.GetFilename() + text.GetFileExtension()] = text_json


    def create_ordered_data_structures(self):

        # Dictionary of topic proportions keyed on filename
        for text_filename in self.m_twic_texts_json:
            found = False
            for tp in self.m_topics_file_data:
                if tp.fileid + ".txt" == text_filename:
                    self.m_text_topicweights[text_filename] = tp.topic_guide
                    found = True
                    break
            if not found:
                raise IOError("Could not find {0}".format(text_filename))

        # Create an ordered topic word weight list (this will be used to rank topic words within their topic)
        self.m_ord_words_in_topics = [[] for index in range(self.m_topic_count)]
        for int_topic_id in range(self.m_topic_count):

            str_topic_id = str(int_topic_id)

            for word in self.m_wordweights_table[str_topic_id]:
                self.m_ord_words_in_topics[int_topic_id].append([word, self.m_wordweights_table[str_topic_id][word], -1])
            self.m_ord_words_in_topics[int_topic_id] = sorted(self.m_ord_words_in_topics[int_topic_id], key=lambda x: x[1], reverse=True)

            # This determines rank based on weight, similar weights get same rank
            rank_index = 1
            current_weight = self.m_ord_words_in_topics[int_topic_id][0][1]
            self.m_ord_words_in_topics[int_topic_id][0][2] = rank_index
            for word_index in range(1, len(self.m_ord_words_in_topics[int_topic_id])):
                if current_weight != self.m_ord_words_in_topics[int_topic_id][word_index][1]:
                    rank_index += 1
                    current_weight = self.m_ord_words_in_topics[int_topic_id][word_index][1]
                self.m_ord_words_in_topics[int_topic_id][word_index][2] = rank_index

            # Keeps track of the last rank used per topic for topic words
            self.m_last_topic_word_ranks.append(rank_index)

        # For topic word rank determination optimization
        for index in range(self.m_topic_count):
            self.m_stripped_ord_words_in_topics.append({})
            for index2 in range(len(self.m_ord_words_in_topics[index])):
                word_sans_punc = TWiC_CloseReading.strip_punctuation_lowercase(self.m_ord_words_in_topics[index][index2][0])
                self.m_stripped_ord_words_in_topics[index][word_sans_punc] = self.m_ord_words_in_topics[index][index2][2]

        # Create an ordered topic weight list for texts (this will be used to rank topics by their texts)
        for text_filename in self.m_twic_texts_json:
            if text_filename in self.m_text_topicweights:
                self.m_ord_topics_in_texts[text_filename] = []
                for index in range(self.m_topic_count):
                    self.m_ord_topics_in_texts[text_filename].append([index, self.m_text_topicweights[text_filename][str(index)], -1])
                self.m_ord_topics_in_texts[text_filename] = sorted(self.m_ord_topics_in_texts[text_filename], key=lambda x: x[1], reverse=True)

                # This determines rank based on weight, similar weights get same rank
                rank_index = 1
                current_weight = self.m_ord_topics_in_texts[text_filename][0][1]
                self.m_ord_topics_in_texts[text_filename][0][2] = rank_index
                for index in range(1, len(self.m_ord_topics_in_texts[text_filename])):
                    if current_weight != self.m_ord_topics_in_texts[text_filename][index][1]:
                        rank_index += 1
                        current_weight = self.m_ord_topics_in_texts[text_filename][index][1]
                    self.m_ord_topics_in_texts[text_filename][index][2] = rank_index


    def build_and_write_html_files(self):

        # Generate tags for invisible top topic word lists featured in each HTML file
        self.generate_invisible_html_topic_keys()

        # Read in external JS code for word hover-highlighting
        self.read_hover_code()

        # Generate an HTML file for each corpus text
        for text_filename in self.m_twic_texts_json:

            # file_start_time = GetTime()

            # a. Keep track of number of files outputted (w/ MALLET topic state files)
            # If no data was found for a text in MALLET's topic-state file, continue on to the next text in the corpus
            if None == self.m_twic_texts_json[text_filename]:
                self.m_unprocessed_filenames.append(text_filename)
                continue
            self.m_html_files_output += 1

            # data_structures_start_time = GetTime()

            # b. Create tables for internal topic-word id, and word/weight/rank information (args passed by reference for speed)
            topic_word_id_table, ordered_word_list, present_topics, doc_topic_ranks, topic_word_ranks, word_2_wsp_table = \
                self.create_html_building_data_structures(text_filename)

            # data_structures_end_time = GetTime()

            # html_build_start_time = GetTime()

            # c. Build output HTML lines (args passed by reference for speed)
            output_lines = []
            # print "Building HTML for {0}".format(text_filename)
            self.build_single_html_file(text_filename, topic_word_id_table, ordered_word_list,
                                        present_topics, doc_topic_ranks, topic_word_ranks, word_2_wsp_table, output_lines)
            # print "Finished building HTML for {0}".format(text_filename)

            # html_build_end_time = GetTime()

            # d. Output the HTML file to the given output folder
            self.output_html_file(text_filename, output_lines)

            # file_end_time = GetTime()

            # print "============================"
            # print "Data structures time: {0} seconds".format((data_structures_end_time - data_structures_start_time).total_seconds())
            # print "HTML build time: {0} seconds".format((html_build_end_time - html_build_start_time).total_seconds())
            # print "File time: {0}".format((file_end_time - file_start_time).total_seconds())


    def generate_invisible_html_topic_keys(self):

        # Generate comma-separated, top topic word list p/spans (optimization for later HTML file building)
        # Will be invisible in each file, but made visible upon highlighting
        self.m_csinv_top_topic_word_strs = []
        for index in range(self.m_topic_count):
            self.m_csinv_top_topic_word_strs.append("\t\t\t\t<p><span class=\"invisible_topicwordlist topic{0}\">Topic {0}: {1}</span></p>\n".format(index,
                ", ".join(self.m_topic_list[str(index)])))


    def read_hover_code(self):

        hover_js_filepath = self.m_js_folder + self.m_js_hovercode_filename

        if not os.path.isfile(hover_js_filepath):
            raise IOError("Could not find Hover JavaScript file '{0}' in {1}.".format(self.m_js_hovercode_filename,
                                                                                      self.m_js_folder))

        with open(hover_js_filepath, "rU") as hover_js_file:
            self.m_hover_js_lines = hover_js_file.readlines()
            for index in range(len(self.m_hover_js_lines)):
                self.m_hover_js_lines[index] = "\t\t\t" + self.m_hover_js_lines[index]


    def create_html_building_data_structures(self, p_text_filename):

        # Must be built and returned here since Python does not all parameter reassignment
        topic_word_id_table = {}
        ordered_word_list = []
        present_topics = []
        word_2_wsp_table = {}

        # 1. Saves a list of all topics present in this file [p_present_topics]
        #   - Used for custom file JS code and custom file CSS,
        # 2. Builds a table of unique IDs per unique topic word in this file [p_topic_word_id_table]
        #   - Used for word highlighting in hover code, composite rank list, bottom panel metadata
        # 3. Builds a list ordering words by their composite weight (-1 for non-topic words) [p_ordered_word_list]
        # Uses self.m_twic_texts_json, self.m_text_topicweights, self.m_wordweights_table
        for line_index in range(len(self.m_twic_texts_json[p_text_filename]["document"]["lines_and_colors"])):
            for word_index in range(len(self.m_twic_texts_json[p_text_filename]["document"]["lines_and_colors"][line_index][0])):

                word_index_str = str(word_index)

                # If the word's index is listed in the line's word to topic dict
                if word_index_str in self.m_twic_texts_json[p_text_filename]["document"]["lines_and_colors"][line_index][1]:

                    # Get the word (w/ and w/o punctuation) and the word's topic ID
                    word_topic_id = self.m_twic_texts_json[p_text_filename]["document"]["lines_and_colors"][line_index][1][word_index_str]
                    word = self.m_twic_texts_json[p_text_filename]["document"]["lines_and_colors"][line_index][0][word_index]
                    word_sans_punc = TWiC_CloseReading.strip_punctuation_lowercase(word)

                    # Table for optimization, eliminate redundant word-punctuation stripping operations
                    if word_topic_id not in word_2_wsp_table:
                        word_2_wsp_table[word_topic_id] = {}
                    word_2_wsp_table[word_topic_id][word] = word_sans_punc

                    # Save the topic ID as being present in the text
                    present_topics.append(word_topic_id)

                    # Save the weight for that topic in this text
                    text_topic_weight = self.m_text_topicweights[p_text_filename][word_topic_id]

                    # Save topic word weight for storage/composite weight calculation
                    if word_sans_punc in self.m_wordweights_table[word_topic_id]:
                        topic_word_weight = self.m_wordweights_table[word_topic_id][word_sans_punc]
                    else:
                        # topic_word_weight = TWiC_CloseReading.s_small_word_weight
                        topic_word_weight = self.m_mallet_script.nnp_dict[word_topic_id]

                    # Add this word to the p_topic_word_id_table (assigns class numeric word IDs for highlighting)
                    if word_topic_id not in topic_word_id_table:
                        topic_word_id_table[word_topic_id] = { "last_id": 0 }
                    topic_word_id_table[word_topic_id][word_sans_punc] = topic_word_id_table[word_topic_id]["last_id"]
                    topic_word_id_table[word_topic_id]["last_id"] += 1

                    # Ordered word list is used for composite rank list
                    # 0 - word, 1 - composite weight, 2 - word index in its line,
                    # 3 - word's line index, 4 - composite rank, 5 word's topic ID
                    ordered_word_list.append([word, text_topic_weight * topic_word_weight, word_index, line_index, -1, word_topic_id])
                else:
                    word = self.m_twic_texts_json[p_text_filename]["document"]["lines_and_colors"][line_index][0][word_index]
                    ordered_word_list.append([word, -1, word_index, line_index, -1, -1])

        # Sort word tuples by composite weights (for composite rank ordering)
        ordered_word_list = sorted(ordered_word_list, key=lambda x: x[1], reverse=True)

        # This determines rank based on composite weight, similar weights get same rank
        rank_index = 1
        current_weight = ordered_word_list[0][1]
        ordered_word_list[0][4] = rank_index
        for index in range(1, len(ordered_word_list)):
            if current_weight != ordered_word_list[index][1]:
                rank_index += 1
                current_weight = ordered_word_list[index][1]
            ordered_word_list[index][4] = rank_index

        # Make a set of all topics present in this file
        present_topics = list(set(present_topics))

        # Determine the topic's rank among the document's topics
        doc_topic_ranks = [-1] * self.m_topic_count
        for index in range(len(doc_topic_ranks)):
            for index2 in range(len(self.m_ord_topics_in_texts[p_text_filename])):
                if index == self.m_ord_topics_in_texts[p_text_filename][index2][0]:
                    doc_topic_ranks[index] = self.m_ord_topics_in_texts[p_text_filename][index2][2]

        # Determine topic word ranks for all words in the document
        topic_word_ranks = {}
        for index in range(len(ordered_word_list)):

            str_topic_id = ordered_word_list[index][5]
            if -1 == str_topic_id:
                continue
            int_topic_id = int(str_topic_id)
            word = ordered_word_list[index][0]
            word_sans_punc = word_2_wsp_table[str_topic_id][word]

            if str_topic_id not in topic_word_ranks:
                topic_word_ranks[str_topic_id] = {}

            try:
                topic_word_ranks[str_topic_id][word_sans_punc] = self.m_stripped_ord_words_in_topics[int_topic_id][word_sans_punc]
            except:
                topic_word_ranks[str_topic_id][word_sans_punc] = self.m_last_topic_word_ranks[int_topic_id] + 1
            # if word_sans_punc in self.m_stripped_ord_words_in_topics[int_topic_id]:
            #     topic_word_ranks[str_topic_id][word_sans_punc] = self.m_stripped_ord_words_in_topics[int_topic_id][word_sans_punc]
            # else:
            #     topic_word_ranks[str_topic_id][word_sans_punc] = self.m_last_topic_word_ranks[int_topic_id] + 1

        return topic_word_id_table, ordered_word_list, present_topics, doc_topic_ranks, topic_word_ranks, word_2_wsp_table


    def build_single_html_file(self, p_text_filename, p_topic_word_id_table, p_ordered_word_list,
                               p_present_topics, p_doc_topic_ranks, p_topic_word_ranks, word_2_wsp_table, p_output_lines):

        p_output_lines.append(("<!DOCTYPE html>\n"
                               "<html>\n"

                               # Header starts here
                               "\t<head>\n"
                               "\t\t<meta charset=\"utf-8\">\n"
                               "\t\t<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"

                               # All JS and CSS are stored within the output folder for ease of use, copying, etc.
                               "\t\t<link rel=\"stylesheet\" type=\"text/css\" href=\"bootstrap.min.css\">\n"
                               "\t\t<link rel=\"stylesheet\" type=\"text/css\" href=\"twic_close_reading.css\">\n"
                               "\t\t<script src=\"jquery-3.2.1.min.js\"></script>\n"
                               "\t\t<script src=\"bootstrap.min.js\"></script>\n"))

        # Hover/custom topic word highlighting JS code
        p_output_lines.append("\t\t<script>\n")
        p_output_lines.extend(self.m_hover_js_lines)
        p_output_lines.append(("\n\n"
                               "\t\t\t$(function(){\n\n"))

        # Code assigning hover code and CSS color for spans tagged by topic
        for index in range(len(p_present_topics)):
            p_output_lines.append(("\t\t\t\t$(\"span.topic{0}\").hover(HoverEnter, HoverExit);\n"
                                   "\t\t\t\ttopicColorTable[\"topic{0}\"] = $(\"span.topic{0}\").css(\"color\");\n").format(p_present_topics[index]))
        p_output_lines.append(("\t\t\t});\n"
                               "\t\t</script>\n"))

        # Output custom CSS for topic colors (spans classed as topicN)
        p_output_lines.append("\t\t<style>\n")
        for index in range(len(p_present_topics)):
            p_output_lines.append(("\t\t\t.topic{0} {{\n"
                                   "\t\t\t\tcolor: {1};\n").format(p_present_topics[index], self.m_color_list_str[p_present_topics[index]]))
            p_output_lines.append("\t\t\t}\n\n")
        p_output_lines.append(("\t\t</style>\n"
                               "\t</head>\n"))

        # Body starts here
        p_output_lines.append(("\t<body>\n"
                               "\t\t<div class=\"container-fluid\">\n"
                               "\t\t\t<div class=\"row table-row\">\n"
                               "\t\t\t\t<div class=\"col-xs-{0} col-sm-{0} col-md-{0} col-lg-{0} fulltext\">\n").format(self.m_twitter_bootstrap_dims["cols_text"]))

        # Builds human-authored text with topic and non-topic words in left panel
        # Uses self.m_twic_texts_json, self.m_color_list_str, self.m_text_topicweights, topic_word_id_table
        for line_index in range(len(self.m_twic_texts_json[p_text_filename]["document"]["lines_and_colors"])):

            p_output_lines.append("\t\t\t\t\t<p>")

            for word_index in range(len(self.m_twic_texts_json[p_text_filename]["document"]["lines_and_colors"][line_index][0])):

                word_index_str = str(word_index)

                if word_index_str in self.m_twic_texts_json[p_text_filename]["document"]["lines_and_colors"][line_index][1]:

                    word_topic_id = self.m_twic_texts_json[p_text_filename]["document"]["lines_and_colors"][line_index][1][word_index_str]
                    word = self.m_twic_texts_json[p_text_filename]["document"]["lines_and_colors"][line_index][0][word_index]
                    # word_sans_punc = TWiC_CloseReading.strip_punctuation_lowercase(word)
                    # word_2_wsp_table[word] = TWiC_CloseReading.strip_punctuation_lowercase(word)

                    p_output_lines.append("<span class=\"topicword topic{0} topic{1}_{2}\" style=\"color:{3};\">{4}</span><span>&nbsp;</span>".format(
                        word_topic_id,
                        word_topic_id,
                        # p_topic_word_id_table[word_topic_id][word_sans_punc],
                        p_topic_word_id_table[word_topic_id][word_2_wsp_table[word_topic_id][word]],
                        self.m_color_list_str[word_topic_id],
                        word))

                else:
                    p_output_lines.append("<span class=\"normword\">{0}</span><span>&nbsp;</span>".format(
                        self.m_twic_texts_json[p_text_filename]["document"]["lines_and_colors"][line_index][0][word_index]))
            p_output_lines.append("</p><br/>\n")


        # End text and begin composite rank list
        p_output_lines.append(("\t\t\t\t</div>\n" # End Column
                               "\t\t\t\t<div class=\"col-xs-{0} col-sm-{0} col-md-{0} col-lg-{0} wordweightcolumn\">\n").format(self.m_twitter_bootstrap_dims["cols_comprank_list"]))

        # Composite rank list header information
        p_output_lines.append("\t\t\t\t\t<p><span class=\"normword\">Composite Rank. (doc topic rank, topic word rank)</span></p><br/>\n")

        # Builds composite rank list
        # Going through word list ordered by composite weight (in reverse)
        # Uses p_ordered_word_list, self.m_twic_texts_json, self.m_color_list_int, self.m_ord_topics_in_texts, self.m_ord_words_in_topics, p_topic_word_id_table
        for index in range(len(p_ordered_word_list)):

            if str(p_ordered_word_list[index][2]) in self.m_twic_texts_json[p_text_filename]["document"]["lines_and_colors"][p_ordered_word_list[index][3]][1]:

                # Get topic ID and color
                word_topic_id = self.m_twic_texts_json[p_text_filename]["document"]["lines_and_colors"][p_ordered_word_list[index][3]][1][str(p_ordered_word_list[index][2])]
                word_topic_id_int = int(word_topic_id)
                # word_color = self.m_color_list_int[word_topic_id_int]

                # Get lowercase word without punctuation on the ends
                # word_sans_punc = TWiC_CloseReading.strip_punctuation_lowercase(p_ordered_word_list[index][0])
                word_sans_punc = word_2_wsp_table[word_topic_id][p_ordered_word_list[index][0]]

                # Composite rank is based on the changes in composite weight in the ordered word list
                # composite_rank = p_ordered_word_list[index][4]

                # The topic's rank among the document's topics
                # doc_topic_rank = p_doc_topic_ranks[word_topic_id_int]

                # The word's rank among the topic's words
                topic_word_rank = p_topic_word_ranks[word_topic_id][word_sans_punc]
                # If the word has near-nil probability within its topic, it receives the lowest rank possible
                # if -1 == topic_word_rank:
                #     topic_word_rank = self.m_last_topic_word_ranks[word_topic_id_int] + 1

                p_output_lines.append("\t\t\t\t\t<p><span class=\"topicword topic{0} topic{0}_{1}\" style=\"color:{2}\">{3}. {4} ({5}, {6})</span></p><br/>\n".format(
                    word_topic_id,
                    p_topic_word_id_table[word_topic_id][TWiC_CloseReading.strip_punctuation_lowercase(p_ordered_word_list[index][0])],
                    # word_color,
                    self.m_color_list_int[word_topic_id_int],
                    # composite_rank,
                    p_ordered_word_list[index][4],
                    word_sans_punc,
                    # doc_topic_rank,
                    p_doc_topic_ranks[word_topic_id_int],
                    topic_word_rank))

        p_output_lines.append(("\t\t\t\t</div>\n" # End Column
                               "\t\t\t</div>\n" # End Row
                               "\t\t</div>\n" # End Container

                               # Metdata panel on bottom of window
                               "\t\t<footer class=\"footer\">\n"
                               "\t\t\t<div class\"container-fluid\">\n"

                               # Topic word list uses bootstrap's full 12 columns
                               "\t\t\t\t<div class=\"row\">\n"
                               "\t\t\t\t\t<p><span class=\"topicword topicwordlist\">Topic Word List</span></p><br/>\n"
                               "\t\t\t\t</div>\n"

                               "\t\t\t\t<div class=\"row meta_row\">\n"

                               "\t\t\t\t\t<div class=\"col-xs-{0} col-sm-{0} col-md-{0} col-lg-{0}\">\n"
                               "\t\t\t\t\t\t<p><span class=\"normword meta_label\">Word:&nbsp;</span>"
                               "<span class=\"meta_topicword\"></span></p><br/>\n"
                               "\t\t\t\t\t</div>").format(self.m_twitter_bootstrap_dims["cols_meta_topicword"])) # End Col for topic word meta text

        p_output_lines.append(("\t\t\t\t\t<div class=\"col-xs-{0} col-sm-{0} col-md-{0} col-lg-{0}\">\n"
                               "\t\t\t\t\t\t<p><span class=\"normword meta_label\">Composite Rank:&nbsp;</span>"
                               "<span class=\"topicword compositerank\"></span></p><br/>\n"
                               "\t\t\t\t\t\t<p><span class=\"normword meta_label\">Document-Topic Rank:&nbsp;</span>"
                               "<span class=\"topicword doctopicrank\"></span></p><br/>\n"
                               "\t\t\t\t\t\t<p><span class=\"normword meta_label\">Topic-Word Rank:&nbsp;</span>"
                               "<span class=\"topicword topicwordrank\"></span></p><br/>\n"
                               "\t\t\t\t\t</div>\n" # End Col for rank meta text
                               "\t\t\t\t</div>\n").format(self.m_twitter_bootstrap_dims["cols_meta_ranks"]))  # End Row

        # Invisible topic word lists - their text will go into the visible topic word list span
        p_output_lines.extend(self.m_csinv_top_topic_word_strs)

        # Invisible word stats - their text will go into the visible topic word list span
        # Uses p_ordered_word_list, self.m_twic_texts_json, self.m_color_list_str, self.m_topic_count,
        #      self.m_ord_topics_in_texts, self.m_ord_words_in_topics, p_topic_word_id_table
        for index in range(len(p_ordered_word_list)):

            if str(p_ordered_word_list[index][2]) in self.m_twic_texts_json[p_text_filename]["document"]["lines_and_colors"][p_ordered_word_list[index][3]][1]:

                word_topic_id = self.m_twic_texts_json[p_text_filename]["document"]["lines_and_colors"][p_ordered_word_list[index][3]][1][str(p_ordered_word_list[index][2])]
                word_topic_id_int = int(word_topic_id)
                # word_color = self.m_color_list_str[word_topic_id]

                # word_sans_punc = TWiC_CloseReading.strip_punctuation_lowercase(p_ordered_word_list[index][0])
                word_sans_punc = word_2_wsp_table[word_topic_id][p_ordered_word_list[index][0]]

                # composite_rank = p_ordered_word_list[index][4]

                # The topic's rank among the document's topics
                # doc_topic_rank = p_doc_topic_ranks[word_topic_id_int]

                # The word's rank among the topic's words
                topic_word_rank = p_topic_word_ranks[word_topic_id][word_sans_punc]
                # If the word has near-nil probability within its topic, it receives the lowest rank possible
                # if -1 == topic_word_rank:
                #     topic_word_rank = self.m_last_topic_word_ranks[word_topic_id_int] + 1

                p_output_lines.append("\t\t\t\t<p><span class=\"invisible_topicword topic{0} topic{0}_{1}\">{2}</span></p>\n".format(
                    word_topic_id,
                    p_topic_word_id_table[word_topic_id][word_sans_punc],
                    word_sans_punc))
                p_output_lines.append("\t\t\t\t<p><span class=\"invisible_compositerank topic{0} topic{0}_{1}\">{2}</span></p>\n".format(
                    word_topic_id,
                    p_topic_word_id_table[word_topic_id][word_sans_punc],
                    # composite_rank))
                    p_ordered_word_list[index][4]))
                p_output_lines.append("\t\t\t\t<p><span class=\"invisible_doctopicrank topic{0} topic{0}_{1}\">{2}</span></p>\n".format(
                    word_topic_id,
                    p_topic_word_id_table[word_topic_id][word_sans_punc],
                    # doc_topic_rank))
                    p_doc_topic_ranks[word_topic_id_int]))
                p_output_lines.append("\t\t\t\t<p><span class=\"invisible_topicwordrank topic{0} topic{0}_{1}\">{2}</span></p>\n".format(
                    word_topic_id,
                    p_topic_word_id_table[word_topic_id][word_sans_punc],
                    topic_word_rank))

        p_output_lines.append(("\t\t\t</div>\n" # End Container
                               "\t\t</footer>\n" # End Footer
                               "\t</body>\n"
                               "</html>"))


    def output_html_file(self, p_text_filename, p_output_lines):

        # Write all lines at once (for speed)
        with open(self.m_yaml_config["output_path"] + os.path.splitext(p_text_filename)[0] + ".html", "w") as output_html_file:
            output_html_file.writelines(p_output_lines)


    def output_unprocessed_file(self):

        # Write out the names of corpus files without MALLET state data (and thus no built HTML files)
        with open(self.m_tcr_root_folder + self.m_tcr_unprocessed_filename, "w") as unprocessed_file:
            unprocessed_file.write("Could not make HTML files for the following.\n")
            unprocessed_file.write("The MALLET state file contained no data for them.\n")
            for filename in self.m_unprocessed_filenames:
                unprocessed_file.write("{0}\n".format(filename))


    def print_building_statistics(self):

        print "Finished building HTML files for MALLET topic model of {0}.".format(self.m_yaml_config["corpus_title"])
        print "Created {0} TWiC close reading HTML files in {1}.".format(self.m_html_files_output, self.m_yaml_config["output_path"])
        print "Could not find MALLET topic-state data for {0} files in this corpus.".format(len(self.m_twic_texts_json) - self.m_html_files_output)
        print "See tcr_unprocessed.txt for the names of these files."


    # TWiC_MalletScript.GetTopicWordWeights() does not store near nil probability (NNP) topic words.
    # This saves processing time and memory.
    # The assessment of an NNP for a word is made by locating the most highly common small value stored in the
    # topic weight distribution by MALLET, and this assigned weight is used as a means of presuming a NNP.
    # The value below is used as an NNP dummy weight for topic word weights not saved by GetTopicWordWeights().
    # s_small_word_weight = 0.0000000001


    @staticmethod
    def debug_output_composite_rank_list(p_text_filename, p_ordered_word_list):

        for index in range(len(ordered_word_list)):
            word = ordered_word_list[index][0]
            word_sans_punc = TWiC_CloseReading.strip_punctuation_lowercase(word)
            word_topic_id = ordered_word_list[index][5]
            if -1 == word_topic_id:
                continue
            text_topic_weight = self.m_text_topicweights[p_text_filename][word_topic_id]
            if word_sans_punc in self.m_wordweights_table[word_topic_id]:
                topic_word_weight = self.m_wordweights_table[word_topic_id][word_sans_punc]
            else:
                topic_word_weight = self.m_mallet_script.nnp_dict[word_topic_id]
            print "{0}. {1} from {2} with ({3}, {4}, {5})".format(
                ordered_word_list[index][4],
                ordered_word_list[index][0],
                word_topic_id,
                text_topic_weight * topic_word_weight,
                text_topic_weight,
                topic_word_weight)


    @staticmethod
    def ensure_folder_has_endsep(p_foldername):

        # Make sure given string ends in OS-specific folder separator character
        if os.sep != p_foldername[len(p_foldername) - 1]:
            return p_foldername + os.sep
        else:
            return p_foldername


    @staticmethod
    def strip_punctuation_lowercase(p_word):

        # Clear leading/trailing whitespace and punctuation, and make lowercase
        return p_word.strip().strip(string.punctuation).lower()


def main():

    print "\nTopic Words in Context (TWiC) Close Reading"
    print "\tby Jonathan Armoza (github.com/jarmoza), 2017.\n"
    print "This work is licensed under the GNU General Public License, Version 3.0."
    print "See https://www.gnu.org/licenses/gpl-3.0.en.html for details.\n"

    try:
        tcr = TWiC_CloseReading(os.getcwd(), "tcr_config.yaml")

        # 1. Read MALLET filenames, output path
        print "Reading YAML file..."
        tcr.read_yaml()
        # TimeAndCount(tcr.read_yaml, "read_yaml")
        # PrintAndReset()

        # 2. Load MALLET topic model data into TWiC data structures
        print "Reading MALLET model files..."
        tcr.load_topic_model_data()
        # TimeAndCount(tcr.load_topic_model_data, "load_topic_model_data")
        # PrintAndReset()

        # 3. Gather required topic model information into TWiC close reading's data structures
        print "Converting MALLET model into TWiC data structures..."
        tcr.convert_model_data_into_structures()
        # TimeAndCount(tcr.convert_model_data_into_structures, "convert_model_data_into_structures")
        # PrintAndReset()

        # 4. Create close-reading HTML files
        print "Creating close reading HTML files..."
        tcr.build_and_write_html_files()
        # TimeAndCount(tcr.build_and_write_html_files, "build_and_write_html_files")
        # PrintAndReset()

        # 5. Generate a file detailing which text files an HTML file could not be created for
        tcr.output_unprocessed_file()
        # TimeAndCount(tcr.output_unprocessed_file, "output_unprocessed_file")
        # PrintAndReset()

        # 6. Output HTML-building statistics
        tcr.print_building_statistics()

    except Exception as exc:
        print exc.message
        logging.error(traceback.format_exc())


if "__main__" == __name__:
    Utils_MalletInterpret.TimeAndRun(main, "TWiC Close Reading")
