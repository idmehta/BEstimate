# -----------------------------------------------------------------------------------------#
#                                                                                          #
#                                  B E s t i m a t e                                       #
#                        Author : Cansu Dincer cd7@sanger.ac.uk                            #
#                         Dr Matthew Coelho & Dr Mathew Garnett                            #
#                              Wellcome Sanger Institute                                   #
#                                                                                          #
# -----------------------------------------------------------------------------------------#


import argparse, pandas, os

# Extracting Humen Reference Genome

###########################################################################################
# Take inputs

def take_input():
	parser = argparse.ArgumentParser(prog="BEstimate - Genome",
									 usage="%(prog)s [inputs]")

	for group in parser._action_groups:
		if group.title == "optional arguments":
			group.title = "Inputs"
		elif "positional arguments":
			group.title = "Mandatory Inputs"

	parser.add_argument("-pamseq", dest="PAMSEQ", default="NGG",
						help="The PAM sequence in which features used "
							 "for searching activity window and editable nucleotide.")

	parser.add_argument("-assembly", dest="ASSEMBLY", required=True, default="GRCh38",
						help="The genome assembly that will be used!")

	parser.add_argument("-o", dest="OUTPUT_PATH", default=os.getcwd() + "/",
						help="The path for output. If not specified the current directory will be used!")

	parser.add_argument("-v_ensembl", dest="VERSION", default="113",
						help="The ensembl version in which genome will be retrieved "
							 "(if the assembly is GRCh37 then please use <=75)")

	parser.add_argument("-wge_path", dest="WGE_PATH", default=os.getcwd() + "../../CRISPR-Analyser/",
						help="The path where the CRISPR Analyser has been installed.")

	parsed_input = parser.parse_args()
	input_dict = vars(parsed_input)

	return input_dict


###########################################################################################
# Functions

def check_genome_exist(assembly, ens_ver):
	global ot_path
	chromosomes = list(range(1, 23)) + ["X", "Y", "MT"]

	if assembly == "GRCh37":
		file_main_text = "Homo_sapiens.GRCh37.%s.dna.chromosome" % ens_ver
	elif assembly == "GRCh38":
		file_main_text = "Homo_sapiens.GRCh38.dna.chromosome"

	if "%s.all.fa.gz" % file_main_text not in os.listdir("%s/genome/" % ot_path):
		print(
			"Genome is not found, BEstimate is downloading the %s Ensembl genome - version %s\n" % (assembly, ens_ver))
		if "chromosome_ftps.txt" not in os.listdir("%s/genome/" % ot_path):
			f = open("%s/genome/chromosome_ftps.txt" % ot_path, "w")
			for chromosome in chromosomes:
				f.writelines(
					"url=https://ftp.ensembl.org/pub/release-%s/fasta/homo_sapiens/dna/%s.%s.fa.gz\n" % (
						ens_ver, file_main_text, chromosome))
				f.writelines(
					"output=%s/genome/%s.%s.fa.gz\n" % (ot_path, file_main_text, chromosome))
			f.close()

		curl_command = "curl --parallel --parallel-immediate --parallel-max 25 --fail-with-body --retry 5 " \
					   "--config %s/genome/chromosome_ftps.txt -C -" % ot_path
		print("Collecting the genome files from Ensembl FTP..\n")
		_ = subprocess.Popen(curl_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
							 text=True, shell=True)
		check_files = True
		for chromosome in chromosomes:
			if "%s.%s.fa.gz" % (file_main_text, chromosome) not in os.listdir(ot_path + "/genome/"):
				check_files = False

		error_message = "Error in downloading genome, please manually downloading all chromosomes from:" \
						"https://ftp.ensembl.org/pub/release-%s/fasta/homo_sapiens/dna/ named as " \
						"Homo_sapiens.GRCh38.dna.chromosome.<chromosome>.fa.gz if the assembl is GRCh38, otherwise" \
						"Homo_sapiens.GRCh37.<version>.dna.chromosome.<chromosome>.fa.gz"

		if check_files: return True
		else: return error_message


def index_genome_wge(assembly, ens_ver, pam_sequence):
	global ot_path, wge_path
	chromosomes = list(range(1, 23)) + ["X", "Y", "MT"]

	if assembly == "GRCh37":
		file_main_text = "Homo_sapiens.GRCh37.%s.dna.chromosome" % ens_ver
	elif assembly == "GRCh38":
		file_main_text = "Homo_sapiens.GRCh38.dna.chromosome"

	chromosome_input_text_list = list()
	for chromosome in chromosomes:
		chromosome_input_text_list.append("-i %s/genome/csv/c_%s.csv " % (ot_path, chromosome))
	chromosome_input_text = " ".join(chromosome_input_text_list)

	# Gather all chromosome fasta files into cvs files
	for chromosome in chromosomes:
		file_name = "%s.%s.fa" % (file_main_text, chromosome)
		if "c1_%s.csv" % chromosome not in os.listdir("%s/genome/csv/" % ot_path):
			if file_name not in os.listdir("%s/genome/" % ot_path):
				os.system("gunzip --keep %s/genome/%s.gz" % (ot_path, file_name))

		print("Gathering chromosomes..")
		csv_command = "python3 x_gather.py -i '%s/genome/%s' -o '%s/genome/csv/c_%s.csv' -p '%s'" % (
		ot_path, file_name, ot_path, chromosome, pam_sequence)
		csv_process = subprocess.Popen(csv_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
									   stderr=subprocess.PIPE,
									   text=True, shell=True)
		while csv_process.poll() is None:
			time.sleep(0.5)

	os.system("python3 x_index.py %s -d crisprs.db" % chromosome_input_text)

	if "%s.bin" % file_main_text not in os.listdir("%s/genome/" % ot_path):
		# Index genome
		print("%sCRISPR-Analyser/bin/crispr_analyser index -a '%s' -s 'Human' -e '1' %s "
			  "-o '%s/genome/%s.bin'"
			  % (wge_path, ens_ver, chromosome_input_text, ot_path, file_main_text))
		os.system("%sCRISPR-Analyser/bin/crispr_analyser index -a '%s' -s 'Human' -e '1' %s "
				  "-o '%s/genome/%s.bin'"
				  % (wge_path, ens_ver, chromosome_input_text, ot_path, file_main_text))

	if "%s.bin" % file_main_text in os.listdir("%s/genome/" % ot_path):
		return True
	else:
		return False


###########################################################################################
# Execution


def main():
	"""
	Run whole script with the input from terminal
	:return:
	"""

	global args

	is_genome = check_genome_exist(assembly=args["ASSEMBLY"], ens_ver=args["VERSION"])

	if is_genome:	return True
	else:
		print("Error: Please download the Humen Reference Genome from Ensembl before continue!")

	if is_genome:
		print("Indexing the genome..")
		res = index_genome_wge(assembly=args["ASSEMBLY"], ens_ver=args["VERSION"], pam_sequence=args["PAMSEQ"])

	return res


if __name__ == '__main__':

	# -----------------------------------------------------------------------------------------#
	# Retrieve input

	args = take_input()
	# Output Path
	path = ""
	if args["OUTPUT_PATH"][-1] == "/":
		path = args["OUTPUT_PATH"]
	else:
		path = args["OUTPUT_PATH"] + "/"

	ot_path = os.getcwd() + "/../offtargets"

	wge_path = ""
	if args["WGE_PATH"][-1] == "/":
		wge_path = args["WGE_PATH"]
	else:
		wge_path = args["WGE_PATH"] + "/"

	main()
