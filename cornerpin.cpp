#include <iostream>
#include <vector>
#include <opencv2/opencv.hpp>
#include <fstream>
#include <string>
#include <opencv/cv.h>
#include <opencv/ml.h>
#include <opencv/cxcore.h>
#include <opencv/highgui.h>

//#define CP_SHOW
#define CP_OCL

#ifdef CP_OCL
#include <opencv2/ocl/ocl.hpp>
#endif

using namespace cv;

/*
typedef struct remap_map_ {
	cv::Mat xmat;
	cv::Mat ymat;
} remap_map;
*/

/*
remap_map genMapFromHom(cv::Mat H, cv::Point2d size) {
	int xs = size.x;
	int ys = size.y;
}
*/

double timer()
{
	return cv::getTickCount() / cv::getTickFrequency();
}

void cpvid(VideoCapture &invid, VideoWriter &outvid, cv::Mat H) {
#ifdef CP_OCL
	cv::Mat cpuframe;
	cv::ocl::oclMat inframe, outframe, oclH;
	oclH = H;
#else
	cv::Mat inframe, outframe;
#endif	
	
	double starttime = timer();
	double now;
	
	for (int counter = 0; ; counter++) {
#ifdef CP_OCL
		if (!invid.read(cpuframe)) break;
		inframe = cpuframe;
		cv::ocl::warpPerspective(inframe, outframe, oclH, cv::Size(1920,1080));
#else
		if (!invid.read(inframe)) break;
		cv::warpPerspective(inframe, outframe, H, cv::Size(1920,1080));
#endif
#ifdef CP_SHOW
		cv::imshow("Input", inframe);
		cv::imshow("Output", outframe);
		cv::waitKey(1);
#endif
//		outvid.write(outframe);
//		std::cout << outframe.toString();
		now = timer();
		std::cerr 
			<< (counter+1) << " "
			<< (now-starttime) << " "
			<< ((counter+1) / (now-starttime)) << " "
			<< std::endl;
	}
}

int main(int argc, char **argv) {
	int fourcc = CV_FOURCC('M','J','P','G');
	
	VideoCapture invid(argv[9]);
	std::cerr << "reader open? " << (invid.isOpened() ? "yes" : "NO") << std::endl;

	
	VideoWriter outvid(argv[10], 
		fourcc,
		25,
		cv::Size(1920,1080));
	std::cerr << "writer open? " << (outvid.isOpened() ? "yes" : "NO") << std::endl;
	
	
	Point2f inputQuad[4], outputQuad[4];
	
	inputQuad[0] = Point2f(0,0);
	inputQuad[1] = Point2f(invid.get(CV_CAP_PROP_FRAME_WIDTH),0);
	inputQuad[2] = Point2f(0,invid.get(CV_CAP_PROP_FRAME_HEIGHT));
	inputQuad[3] = Point2f(invid.get(CV_CAP_PROP_FRAME_WIDTH),invid.get(CV_CAP_PROP_FRAME_HEIGHT));
	outputQuad[0] = Point2f(atoi(argv[1]),atoi(argv[2])); // ulx, uly
	outputQuad[1] = Point2f(atoi(argv[3]),atoi(argv[4])); // urx, ury
	outputQuad[2] = Point2f(atoi(argv[5]),atoi(argv[6])); // llx, lly
	outputQuad[3] = Point2f(atoi(argv[7]),atoi(argv[8]));  // lrx, lry
	
	std::cerr << "input and output Quad ready" << std::endl;
	
	cv::Mat H = cv::getPerspectiveTransform(inputQuad, outputQuad);
	
	std::cerr << "H ready" << std::endl;
	
	cpvid(invid, outvid, H);
}
